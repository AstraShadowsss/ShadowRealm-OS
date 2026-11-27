#define _DEFAULT_SOURCE
#include <sys/prctl.h>
#include <gtk/gtk.h>
#include <vte/vte.h>
#include <sys/utsname.h>
#include <unistd.h>
#include <locale.h>
#include <stdio.h>
#include <string.h>

static const char *terminal_neon_css="#shadow-root { background: #000000; }"
        "#shadow-header { background: #000000; border-bottom: 2px solid #cf26d7; }"
        ".shadow-title { color: #ff35e1; font-family: 'DejaVu Sans Mono'; font-weight: bold; font-size: 18px; }"
        ".shadow-info { color: #17edff; font-family: 'DejaVu Sans Mono'; font-size: 12px; }"
        ".shadow-caption { color: #c990e5; font-family: 'DejaVu Sans Mono'; font-size: 11px; }"
        ".shadow-tool { background: #231532; color: #d9faff; border: 1px solid #72477f; padding: 3px 9px; }";
static const char *terminal_professional_css="#shadow-root,#shadow-header { background: #000; } #shadow-header { border-bottom: 1px solid @theme_selected_bg_color; } .shadow-title { color: #f1f5f9; font-family: Sans; font-weight: bold; font-size: 18px; } .shadow-info { color: #d2d7dc; font-family: Sans; font-size: 12px; } .shadow-caption { color: #93a8bb; font-size: 11px; } .shadow-tool { background: #252525; color: #f1f5f9; border: 1px solid @theme_selected_bg_color; padding: 4px 9px; }";

/* ShadowRealm-OS Terminal: maintained GTK/VTE application. */
typedef struct {
    GtkWidget *window;
    GtkCssProvider *css;
    GtkWidget *stats;
    GtkWidget *logo_image;
    GtkWidget *notebook;
    GtkWidget *scroll;
    gchar *rc_path;
    VteTerminal *terminal;
    double zoom;
    double background_alpha;
    gboolean fullscreen;
} App;

static void on_spawn(VteTerminal *term, GPid pid, GError *error, gpointer data);
static void on_shell_exit(VteTerminal *term, gint status, gpointer data);

static double terminal_background_opacity(void){int value=90;char*p=g_build_filename(g_get_home_dir(),".config","shadowrealm-os","transparency.ini",NULL);GKeyFile*k=g_key_file_new();if(g_key_file_load_from_file(k,p,G_KEY_FILE_NONE,NULL)&&g_key_file_has_key(k,"Appearance","terminal-opacity",NULL))value=g_key_file_get_integer(k,"Appearance","terminal-opacity",NULL);g_key_file_unref(k);g_free(p);return gdk_screen_is_composited(gdk_screen_get_default())?CLAMP(value,0,100)/100.:1.;}
static gboolean transparency_tick(gpointer data){App*a=data;double alpha=terminal_background_opacity();if(a->background_alpha!=alpha){a->background_alpha=alpha;GdkRGBA bg={0,0,0,alpha};int pages=a->notebook?gtk_notebook_get_n_pages(GTK_NOTEBOOK(a->notebook)):0;for(int i=0;i<pages;i++){VteTerminal*t=VTE_TERMINAL(gtk_notebook_get_nth_page(GTK_NOTEBOOK(a->notebook),i));if(t)vte_terminal_set_color_background(t,&bg);}}return G_SOURCE_CONTINUE;}
static GtkWidget *info_label(const char *text, const char *style) {
    GtkWidget *w = gtk_label_new(text);
    gtk_label_set_xalign(GTK_LABEL(w), 0);
    gtk_label_set_ellipsize(GTK_LABEL(w), PANGO_ELLIPSIZE_END);
    gtk_widget_set_halign(w, GTK_ALIGN_FILL);
    gtk_style_context_add_class(gtk_widget_get_style_context(w), style);
    return w;
}

static double used_ram(void) {
    FILE *f = fopen("/proc/meminfo", "r");
    if (!f) return -1;
    char line[256];
    unsigned long total = 0, avail = 0;
    while (fgets(line, sizeof(line), f)) {
        if (sscanf(line, "MemTotal: %lu", &total) == 1) continue;
        if (sscanf(line, "MemAvailable: %lu", &avail) == 1) continue;
    }
    fclose(f);
    return total ? 100.0 * (total - avail) / total : -1;
}

static double uptime_hours(void) {
    double secs = 0;
    FILE *f = fopen("/proc/uptime", "r");
    if (f) { if (fscanf(f, "%lf", &secs) != 1) secs = 0; fclose(f); }
    return secs / 3600.0;
}

static gboolean refresh_stats(gpointer user_data) {
    App *a = user_data;
    char line[256];
    long cores = sysconf(_SC_NPROCESSORS_ONLN);
    double ram = used_ram(), up = uptime_hours();
    if (ram < 0)
        snprintf(line, sizeof(line), "CPU  %ld cores    RAM  unavailable    UPTIME  %.1f h", cores, up);
    else
        snprintf(line, sizeof(line), "CPU  %ld cores    RAM  %.0f%% used    UPTIME  %.1f h", cores, ram, up);
    gtk_label_set_text(GTK_LABEL(a->stats), line);
    return G_SOURCE_CONTINUE;
}

static void set_zoom(App *a, double z) {
    if (z < 0.75) z = 0.75;
    if (z > 1.65) z = 1.65;
    a->zoom = z;
    int pages=a->notebook?gtk_notebook_get_n_pages(GTK_NOTEBOOK(a->notebook)):0;
    for(int i=0;i<pages;i++){VteTerminal*t=VTE_TERMINAL(gtk_notebook_get_nth_page(GTK_NOTEBOOK(a->notebook),i));if(t)vte_terminal_set_font_scale(t,a->zoom);}
    if(a->terminal)gtk_widget_grab_focus(GTK_WIDGET(a->terminal));
}

static gboolean restore_button(gpointer data) {
    GtkButton *b=GTK_BUTTON(data);
    const char *label=g_object_get_data(G_OBJECT(b),"feedback-label");
    if(label) gtk_button_set_label(b,label);
    gtk_style_context_remove_class(gtk_widget_get_style_context(GTK_WIDGET(b)),"suggested-action");
    g_object_set_data(G_OBJECT(b),"feedback-timer",NULL);
    return G_SOURCE_REMOVE;
}
static void button_feedback(GtkButton *b,const char *message) {
    if(!b) return;
    if(!g_object_get_data(G_OBJECT(b),"feedback-label"))
        g_object_set_data_full(G_OBJECT(b),"feedback-label",g_strdup(gtk_button_get_label(b)),g_free);
    guint previous=GPOINTER_TO_UINT(g_object_get_data(G_OBJECT(b),"feedback-timer"));
    if(previous) g_source_remove(previous);
    gtk_button_set_label(b,message);
    gtk_style_context_add_class(gtk_widget_get_style_context(GTK_WIDGET(b)),"suggested-action");
    guint id=g_timeout_add_full(G_PRIORITY_DEFAULT,850,restore_button,g_object_ref(b),g_object_unref);
    g_object_set_data(G_OBJECT(b),"feedback-timer",GUINT_TO_POINTER(id));
}
static void zoom_in(GtkButton *button, gpointer user_data) { (void)button; App *a=user_data; set_zoom(a, a->zoom+0.1); button_feedback(button,"Larger"); }
static void zoom_out(GtkButton *button, gpointer user_data) { (void)button; App *a=user_data; set_zoom(a, a->zoom-0.1); button_feedback(button,"Smaller"); }
static void copy_selection(GtkButton *button, gpointer user_data) {
    (void)button; App *a=user_data;
    button_feedback(button,vte_terminal_get_has_selection(a->terminal)?"Copied":"Select text first");
    vte_terminal_copy_clipboard_format(a->terminal, VTE_FORMAT_TEXT);
    gtk_widget_grab_focus(GTK_WIDGET(a->terminal));
}
static void paste_clipboard(GtkButton *button, gpointer user_data) {
    (void)button; App *a=user_data;
    vte_terminal_paste_clipboard(a->terminal);
    button_feedback(button,"Pasted");
    gtk_widget_grab_focus(GTK_WIDGET(a->terminal));
}
static void clear_terminal(GtkButton *button, gpointer user_data) {
    (void)button; App *a=user_data;
    vte_terminal_reset(a->terminal, FALSE, TRUE);
    button_feedback(button,"Cleared");
    gtk_widget_grab_focus(GTK_WIDGET(a->terminal));
}

static void terminal_theme_changed(GtkSettings *settings,GParamSpec *spec,gpointer data);

static void tab_close_clicked(GtkButton *button, gpointer data) {
    App *a = data;
    VteTerminal *term = g_object_get_data(G_OBJECT(button), "terminal");
    int index = gtk_notebook_page_num(GTK_NOTEBOOK(a->notebook), GTK_WIDGET(term));
    if (index >= 0) gtk_notebook_remove_page(GTK_NOTEBOOK(a->notebook), index);
    if (gtk_notebook_get_n_pages(GTK_NOTEBOOK(a->notebook)) == 0) gtk_widget_destroy(a->window);
}

static void close_current_tab(App *a) {
    int index = gtk_notebook_get_current_page(GTK_NOTEBOOK(a->notebook));
    if (index >= 0) gtk_notebook_remove_page(GTK_NOTEBOOK(a->notebook), index);
    if (gtk_notebook_get_n_pages(GTK_NOTEBOOK(a->notebook)) == 0) gtk_widget_destroy(a->window);
}

static void switch_tab(App *a, int direction) {
    int pages = gtk_notebook_get_n_pages(GTK_NOTEBOOK(a->notebook));
    if (pages < 2) return;
    int index = gtk_notebook_get_current_page(GTK_NOTEBOOK(a->notebook));
    gtk_notebook_set_current_page(GTK_NOTEBOOK(a->notebook), (index + direction + pages) % pages);
}

static void on_tab_switched(GtkNotebook *notebook, GtkWidget *page, guint index, gpointer data) {
    (void)notebook; (void)index;
    App *a = data;
    if (!page || !GTK_IS_WIDGET(page)) return;
    a->terminal = VTE_TERMINAL(page);
    if (a->scroll)
        gtk_range_set_adjustment(GTK_RANGE(a->scroll), gtk_scrollable_get_vadjustment(GTK_SCROLLABLE(page)));
    gtk_widget_grab_focus(page);
}

static GtkWidget *tab_label(App *a, VteTerminal *term, int number) {
    GtkWidget *box = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 6);
    gchar *text = g_strdup_printf("Terminal %d", number);
    GtkWidget *label = gtk_label_new(text);
    g_free(text);
    gtk_box_pack_start(GTK_BOX(box), label, FALSE, FALSE, 0);
    GtkWidget *close = gtk_button_new_from_icon_name("window-close-symbolic", GTK_ICON_SIZE_MENU);
    gtk_button_set_relief(GTK_BUTTON(close), GTK_RELIEF_NONE);
    gtk_widget_set_tooltip_text(close, "Close this terminal tab");
    g_object_set_data(G_OBJECT(close), "terminal", term);
    g_signal_connect(close, "clicked", G_CALLBACK(tab_close_clicked), a);
    gtk_box_pack_start(GTK_BOX(box), close, FALSE, FALSE, 0);
    gtk_widget_show_all(box);
    return box;
}

static void configure_terminal(App *a, VteTerminal *terminal) {
    gtk_widget_set_hexpand(GTK_WIDGET(terminal), TRUE);
    gtk_widget_set_vexpand(GTK_WIDGET(terminal), TRUE);
    PangoFontDescription *font = pango_font_description_from_string("DejaVu Sans Mono 11");
    vte_terminal_set_font(terminal, font);
    pango_font_description_free(font);
    GdkRGBA fg,bg,cursor;
    gdk_rgba_parse(&fg,"#d9faff");
    gdk_rgba_parse(&bg,"#000000");bg.alpha=terminal_background_opacity();
    gdk_rgba_parse(&cursor,"#ff35e1");
    vte_terminal_set_colors(terminal,&fg,&bg,NULL,0);
    vte_terminal_set_color_cursor(terminal,&cursor);
    vte_terminal_set_scrollback_lines(terminal,2000);
    vte_terminal_set_audible_bell(terminal,FALSE);
    vte_terminal_set_font_scale(terminal,a->zoom);
    g_signal_connect(terminal,"child-exited",G_CALLBACK(on_shell_exit),a);
}

static void spawn_tab(App *a, const char *directory, gchar **argv) {
    VteTerminal *terminal = VTE_TERMINAL(vte_terminal_new());
    configure_terminal(a, terminal);
    GtkWidget *label = tab_label(a, terminal, gtk_notebook_get_n_pages(GTK_NOTEBOOK(a->notebook)) + 1);
    int index = gtk_notebook_append_page(GTK_NOTEBOOK(a->notebook), GTK_WIDGET(terminal), label);
    gtk_widget_show(GTK_WIDGET(terminal));
    gtk_notebook_set_current_page(GTK_NOTEBOOK(a->notebook), index);
    a->terminal = terminal;
    if (a->scroll)
        gtk_range_set_adjustment(GTK_RANGE(a->scroll), gtk_scrollable_get_vadjustment(GTK_SCROLLABLE(terminal)));
    gchar *args[] = {"/bin/bash", "--rcfile", a->rc_path, "-i", NULL};
    gchar *cwd = directory ? g_strdup(directory) : g_get_current_dir();
    vte_terminal_spawn_async(terminal, VTE_PTY_DEFAULT, cwd, argv ? argv : args, NULL,
        G_SPAWN_SEARCH_PATH, NULL, NULL, NULL, -1, NULL, on_spawn, a);
    g_free(cwd);
    terminal_theme_changed(gtk_settings_get_default(), NULL, a);
    gtk_widget_grab_focus(GTK_WIDGET(terminal));
}

static void new_tab_clicked(GtkButton *button, gpointer data) {
    (void)button;
    spawn_tab(data, NULL, NULL);
}

static gboolean keypress(GtkWidget *widget, GdkEventKey *event, gpointer user_data) {
    (void)widget;
    App *a = user_data;
    guint mods = event->state & (GDK_CONTROL_MASK|GDK_SHIFT_MASK|GDK_MOD1_MASK);
    guint key = gdk_keyval_to_lower(event->keyval);
    /* Paste with plain Ctrl+V too; terminal users expect the usual shortcut. */
    if (mods == GDK_CONTROL_MASK && key == GDK_KEY_v) { paste_clipboard(NULL,a); return TRUE; }
    if (mods == (GDK_CONTROL_MASK|GDK_SHIFT_MASK)) {
        if (key == GDK_KEY_t) { spawn_tab(a, NULL, NULL); return TRUE; }
        if (key == GDK_KEY_w) { close_current_tab(a); return TRUE; }
        if (event->keyval == GDK_KEY_ISO_Left_Tab) { switch_tab(a, -1); return TRUE; }
        if (key == GDK_KEY_c) { copy_selection(NULL,a); return TRUE; }
        if (key == GDK_KEY_v) { paste_clipboard(NULL,a); return TRUE; }
        if (key == GDK_KEY_plus || key == GDK_KEY_equal || key == GDK_KEY_KP_Add) {
            zoom_in(NULL,a); return TRUE;
        }
        if (key == GDK_KEY_minus || key == GDK_KEY_KP_Subtract) { zoom_out(NULL,a); return TRUE; }
    }
    if (event->keyval == GDK_KEY_F11) {
        if (a->fullscreen) gtk_window_unfullscreen(GTK_WINDOW(a->window));
        else gtk_window_fullscreen(GTK_WINDOW(a->window));
        a->fullscreen = !a->fullscreen;
        return TRUE;
    }
    return FALSE;
}

static void on_spawn(VteTerminal *term, GPid pid, GError *error, gpointer data) {
    (void)term; (void)pid;
    if (!error) return;
    App *a = data;
    GtkWidget *d = gtk_message_dialog_new(GTK_WINDOW(a->window), GTK_DIALOG_MODAL,
        GTK_MESSAGE_ERROR, GTK_BUTTONS_CLOSE, "Could not start shell: %s", error->message);
    gtk_dialog_run(GTK_DIALOG(d));
    gtk_widget_destroy(d);
}
static void on_shell_exit(VteTerminal *term, gint status, gpointer data) {
    (void)status;
    App *a = data;
    if (!a->notebook || !GTK_IS_NOTEBOOK(a->notebook)) return;
    int index = gtk_notebook_page_num(GTK_NOTEBOOK(a->notebook), GTK_WIDGET(term));
    if (index < 0) return;
    gtk_notebook_remove_page(GTK_NOTEBOOK(a->notebook), index);
    if (gtk_notebook_get_n_pages(GTK_NOTEBOOK(a->notebook)) == 0) gtk_widget_destroy(a->window);
}
static GtkWidget *toolbar_button(GtkWidget *toolbar, const char *title, GCallback cb, App *a) {
    GtkWidget *b = gtk_button_new_with_label(title);
    gtk_style_context_add_class(gtk_widget_get_style_context(b), "shadow-tool");
    gtk_widget_set_tooltip_text(b, title);
    g_signal_connect(b, "clicked", cb, a);
    gtk_box_pack_start(GTK_BOX(toolbar), b, FALSE, FALSE, 2);
    return b;
}

static void terminal_theme_changed(GtkSettings *settings,GParamSpec *spec,gpointer data){
 (void)spec;App *a=data;gchar *name=NULL;g_object_get(settings,"gtk-theme-name",&name,NULL);
 gboolean professional=name&&strcmp(name,"ShadowRealm-OS-Neon");gboolean unbranded=name&&g_str_has_prefix(name,"ShadowRealm-OS-Professional");g_free(name);
 gtk_css_provider_load_from_data(a->css,professional?terminal_professional_css:terminal_neon_css,-1,NULL);
 GdkRGBA fg,bg,cursor;gdk_rgba_parse(&fg,professional?"#e5e7eb":"#d9faff");gdk_rgba_parse(&bg,"#000000");bg.alpha=terminal_background_opacity();gdk_rgba_parse(&cursor,professional?"#93b7d6":"#ff35e1");
 if(professional && !gtk_style_context_lookup_color(gtk_widget_get_style_context(a->window),"accent_color",&cursor))gtk_style_context_lookup_color(gtk_widget_get_style_context(a->window),"theme_selected_bg_color",&cursor);
 gchar *brand_path=g_build_filename(g_get_home_dir(),".local","share","shadow-link","term.png",NULL);GdkPixbuf*newlogo=gdk_pixbuf_new_from_file_at_scale(brand_path,88,88,TRUE,NULL);if(newlogo&&a->logo_image){gtk_image_set_from_pixbuf(GTK_IMAGE(a->logo_image),newlogo);}if(newlogo)g_object_unref(newlogo);g_free(brand_path);
 if(a->logo_image){gtk_widget_set_no_show_all(a->logo_image,unbranded);gtk_widget_set_visible(a->logo_image,!unbranded);}
 if(a->notebook){int pages=gtk_notebook_get_n_pages(GTK_NOTEBOOK(a->notebook));for(int i=0;i<pages;i++){VteTerminal*t=VTE_TERMINAL(gtk_notebook_get_nth_page(GTK_NOTEBOOK(a->notebook),i));if(t){vte_terminal_set_colors(t,&fg,&bg,NULL,0);vte_terminal_set_color_cursor(t,&cursor);}}}
 {gchar *p=g_build_filename(g_get_home_dir(),".local","share","shadow-link","icons","current","shadow-terminal.png",NULL);gtk_window_set_icon_from_file(GTK_WINDOW(a->window),p,NULL);g_free(p);}
}

int main(int argc, char **argv) {prctl(PR_SET_NAME,"Terminal",0,0,0);
    if(argc>1 && !strcmp(argv[1],"--version")) {
        printf("Terminal (ShadowRealm-OS), VTE %u.%u.%u %s\n",vte_get_major_version(),vte_get_minor_version(),vte_get_micro_version(),vte_get_features());
        return 0;
    }
    if(argc>1 && !strcmp(argv[1],"--help")) {
        puts("Terminal\nUsage: shadow-terminal [--working-directory DIR] [-e PROGRAM [ARGS...]]\n       shadow-terminal --command COMMAND\n       shadow-terminal --version");
        return 0;
    }
    const char *working_directory=NULL,*command_line=NULL,*window_title="Terminal";
    int execute_index=0;
    for(int i=1;i<argc;i++) {
        if((!strcmp(argv[i],"-T")||!strcmp(argv[i],"--title")) && i+1<argc) {window_title=argv[++i];continue;}
        if((!strcmp(argv[i],"-e")||!strcmp(argv[i],"-x")||!strcmp(argv[i],"--execute")) && i+1<argc) {execute_index=i+1;break;}
        if((!strcmp(argv[i],"--command")||!strcmp(argv[i],"-c")) && i+1<argc) {command_line=argv[++i];continue;}
        if(!strcmp(argv[i],"--working-directory") && i+1<argc) {working_directory=argv[++i];continue;}
        if(g_str_has_prefix(argv[i],"--working-directory="))working_directory=argv[i]+20;
    }
    gchar **execute_args=execute_index?g_strdupv(argv+execute_index):NULL;
    setlocale(LC_ALL, "en_US.UTF-8");
    g_set_prgname("Terminal");
    g_set_application_name("Terminal");
    gdk_set_program_class("Terminal");
    gtk_init(&argc, &argv);
    const char *home = g_get_home_dir();
    gchar *modepath=g_build_filename(home,".config","shadowrealm-os","appearance-mode",NULL),*modetext=NULL;
    gboolean professional=g_file_get_contents(modepath,&modetext,NULL,NULL)&&!g_str_has_prefix(modetext,"neon");
    g_free(modepath);g_free(modetext);
    gchar *logo_path = g_build_filename(home,".local","share","shadow-link","term.png",NULL);
    gchar *rc_path = g_build_filename(home,".local","share","shadow-link","terminal.v3.bashrc",NULL);
    if (!g_file_test(logo_path,G_FILE_TEST_IS_REGULAR)) {g_free(logo_path);logo_path=g_strdup("/usr/share/shadowrealm-os/terminal/logo.png");}
    if (!g_file_test(rc_path,G_FILE_TEST_IS_REGULAR)) {g_free(rc_path);rc_path=g_strdup("/usr/share/shadowrealm-os/terminal/bashrc");}
    GError *e = NULL;
    GdkPixbuf *logo = gdk_pixbuf_new_from_file_at_scale(logo_path, 88, 88, TRUE, &e);
    if (!logo) {
        g_printerr("Unable to load the original ShadowRealm-OS PNG: %s\n", e ? e->message : "unknown error");
        g_clear_error(&e);
        g_free(logo_path); g_free(rc_path);
        return 2;
    }
    GtkCssProvider *css = gtk_css_provider_new();
    gtk_css_provider_load_from_data(css,professional?terminal_professional_css:terminal_neon_css,-1,NULL);

    gtk_style_context_add_provider_for_screen(gdk_screen_get_default(),
        GTK_STYLE_PROVIDER(css), GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);
    g_object_unref(css);

    App app = {0};
    app.css=g_object_ref(css);
    app.zoom = 1;
    app.window = gtk_window_new(GTK_WINDOW_TOPLEVEL);
    gtk_window_set_title(GTK_WINDOW(app.window), window_title);
    GdkVisual *rgba=gdk_screen_get_rgba_visual(gtk_widget_get_screen(app.window));if(rgba)gtk_widget_set_visual(app.window,rgba);
    gtk_widget_set_app_paintable(app.window,TRUE);gtk_widget_set_name(app.window,"shadow-terminal-window");
    GtkCssProvider *transparent=gtk_css_provider_new();gtk_css_provider_load_from_data(transparent,"#shadow-terminal-window, #shadow-root {background-color:transparent;background-image:none;} #shadow-header {background-color:rgba(0,0,0,0.98);} vte-terminal, vte-terminal:backdrop {background-color:transparent;color:#e5e7eb;}",-1,NULL);gtk_style_context_add_provider_for_screen(gdk_screen_get_default(),GTK_STYLE_PROVIDER(transparent),GTK_STYLE_PROVIDER_PRIORITY_APPLICATION+1);g_object_unref(transparent);

    gtk_window_set_default_size(GTK_WINDOW(app.window), 930, 560);
    gchar *app_icon=g_build_filename(home,".local","share","shadow-link","icons","current","shadow-terminal.png",NULL);
    if (!gtk_window_set_icon_from_file(GTK_WINDOW(app.window),app_icon,NULL)) gtk_window_set_icon_name(GTK_WINDOW(app.window),"utilities-terminal");
    g_free(app_icon);
    g_signal_connect(app.window,"destroy",G_CALLBACK(gtk_main_quit),NULL);
    g_signal_connect(app.window,"key-press-event",G_CALLBACK(keypress),&app);

    GtkWidget *root = gtk_box_new(GTK_ORIENTATION_VERTICAL, 0);
    gtk_container_add(GTK_CONTAINER(app.window), root);
    gtk_widget_set_name(root, "shadow-root");
    GtkWidget *header = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 13);
    gtk_widget_set_name(header, "shadow-header");
    gtk_widget_set_margin_start(header, 12);
    gtk_widget_set_margin_end(header, 12);
    gtk_widget_set_margin_top(header, 8);
    gtk_widget_set_margin_bottom(header, 8);
    gtk_box_pack_start(GTK_BOX(root), header, FALSE, FALSE, 0);
    GtkWidget *image = gtk_image_new_from_pixbuf(logo);app.logo_image=image;
    gtk_box_pack_start(GTK_BOX(header), image, FALSE, FALSE, 0);
    g_object_unref(logo);

    GtkWidget *info = gtk_box_new(GTK_ORIENTATION_VERTICAL, 3);
    gtk_widget_set_valign(info, GTK_ALIGN_CENTER);
    gtk_box_pack_start(GTK_BOX(header), info, TRUE, TRUE, 0);
    gtk_box_pack_start(GTK_BOX(info), info_label("ShadowRealm-OS  //  System Information", "shadow-title"), FALSE, FALSE, 0);
    struct utsname un = {0};
    uname(&un);
    char buf[256];
    snprintf(buf,sizeof(buf),"OS  ShadowRealm-OS Linux    KERNEL  %.95s",un.release);
    gtk_box_pack_start(GTK_BOX(info), info_label(buf,"shadow-info"), FALSE,FALSE,0);
    gtk_box_pack_start(GTK_BOX(info), info_label("DESKTOP  XFCE / Shadow Link    TERMINAL  VTE / GTK3","shadow-info"), FALSE,FALSE,0);
    app.stats = info_label("", "shadow-info");
    gtk_box_pack_start(GTK_BOX(info),app.stats,FALSE,FALSE,0);
    gtk_box_pack_start(GTK_BOX(info), info_label("// SHADOW LINK //", "shadow-caption"), FALSE,FALSE,0);

    GtkWidget *tools = gtk_box_new(GTK_ORIENTATION_VERTICAL, 3);
    gtk_widget_set_valign(tools, GTK_ALIGN_CENTER);
    gtk_box_pack_end(GTK_BOX(header), tools, FALSE, FALSE, 0);
    GtkWidget *r1 = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 3);
    GtkWidget *r2 = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 3);
    gtk_box_pack_start(GTK_BOX(tools),r1,FALSE,FALSE,0);
    gtk_box_pack_start(GTK_BOX(tools),r2,FALSE,FALSE,0);
    toolbar_button(r1,"Copy",G_CALLBACK(copy_selection),&app);
    toolbar_button(r1,"Paste",G_CALLBACK(paste_clipboard),&app);
    toolbar_button(r2,"A-",G_CALLBACK(zoom_out),&app);
    toolbar_button(r2,"A+",G_CALLBACK(zoom_in),&app);
    toolbar_button(r2,"Clear",G_CALLBACK(clear_terminal),&app);

    GtkWidget *term_row = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 0);
    gtk_widget_set_margin_start(term_row, 8);
    gtk_widget_set_margin_end(term_row, 4);
    gtk_widget_set_margin_top(term_row, 6);
    gtk_widget_set_margin_bottom(term_row, 6);
    gtk_box_pack_start(GTK_BOX(root), term_row, TRUE, TRUE, 0);
    app.notebook = gtk_notebook_new();
    gtk_notebook_set_scrollable(GTK_NOTEBOOK(app.notebook), TRUE);
    gtk_notebook_set_show_border(GTK_NOTEBOOK(app.notebook), FALSE);
    gtk_widget_set_hexpand(app.notebook, TRUE);
    gtk_widget_set_vexpand(app.notebook, TRUE);
    gtk_box_pack_start(GTK_BOX(term_row), app.notebook, TRUE, TRUE, 0);
    g_signal_connect(app.notebook, "switch-page", G_CALLBACK(on_tab_switched), &app);
    GtkWidget *new_tab = gtk_button_new_from_icon_name("list-add-symbolic", GTK_ICON_SIZE_MENU);
    gtk_button_set_relief(GTK_BUTTON(new_tab), GTK_RELIEF_NONE);
    gtk_widget_set_tooltip_text(new_tab, "New terminal tab (Ctrl+Shift+T)");
    g_signal_connect(new_tab, "clicked", G_CALLBACK(new_tab_clicked), &app);
    gtk_notebook_set_action_widget(GTK_NOTEBOOK(app.notebook), new_tab, GTK_PACK_END);
    gtk_widget_show(new_tab);
    app.scroll = gtk_scrollbar_new(GTK_ORIENTATION_VERTICAL, NULL);
    gtk_box_pack_start(GTK_BOX(term_row), app.scroll, FALSE, FALSE, 0);
    app.rc_path = rc_path;

    g_signal_connect(gtk_settings_get_default(),"notify::gtk-theme-name",G_CALLBACK(terminal_theme_changed),&app);
    terminal_theme_changed(gtk_settings_get_default(),NULL,&app);
    refresh_stats(&app);
    g_timeout_add_seconds(10,refresh_stats,&app);
    transparency_tick(&app);g_timeout_add_seconds(1,transparency_tick,&app);
    gtk_widget_show_all(app.window);
    gchar *command_args[]={"/bin/bash","-lc",(gchar*)command_line,NULL};
    spawn_tab(&app, working_directory, execute_args?execute_args:command_line?command_args:NULL);
    gtk_main();
    g_free(logo_path);
    g_free(rc_path);
    g_strfreev(execute_args);
    g_object_unref(app.css);
    return 0;
}


