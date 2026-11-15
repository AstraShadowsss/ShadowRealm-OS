static const char*basefile(const char*name){static char p[4096];snprintf(p,sizeof p,"%s/.local/share/shadow-link/%s",g_get_home_dir(),name);return p;}
static int prepare_icons(void){GError*e=NULL;GdkPixbuf*p=gdk_pixbuf_new_from_file(basefile("logo.png"),&e);if(!p){fprintf(stderr,"Logo: %s\n",e?e->message:"not found");return 1;}GdkPixbuf*q=gdk_pixbuf_scale_simple(p,64,64,GDK_INTERP_BILINEAR);gdk_pixbuf_save(q,basefile("icons/shadow-menu.png"),"png",NULL,NULL);g_object_unref(q);g_object_unref(p);return 0;}
static int fetch(void){GdkPixbuf*p=gdk_pixbuf_new_from_file(basefile("logo.png"),NULL);if(!p)return 1;GdkPixbuf*q=gdk_pixbuf_scale_simple(p,30,28,GDK_INTERP_BILINEAR);g_object_unref(p);struct utsname un;uname(&un);char host[128];gethostname(host,sizeof host);host[sizeof host-1]=0;char meta[14][160];memset(meta,0,sizeof meta);snprintf(meta[0],sizeof meta[0],"%s@%s",g_get_user_name(),host);strcpy(meta[1],"------------------------------");strcpy(meta[2],"OS:     ShadowRealm-OS Linux");snprintf(meta[3],sizeof meta[3],"KERNEL: %.28s",un.release);strcpy(meta[4],"DE:     XFCE / Shadow Link");strcpy(meta[5],"WM:     Xfwm4");strcpy(meta[6],"THEME:  ShadowRealm-OS Neon");strcpy(meta[7],"ICONS:  ShadowRealm-OS Cyber");strcpy(meta[8],"TERM:   ShadowRealm-OS / VTE");double up=0;FILE*f=fopen("/proc/uptime","r");if(f){fscanf(f,"%lf",&up);fclose(f);}snprintf(meta[9],sizeof meta[9],"UPTIME: %dd %dh %dm",(int)up/86400,(int)up/3600%24,(int)up/60%60);snprintf(meta[10],sizeof meta[10],"CPU:    %ld logical cores",sysconf(_SC_NPROCESSORS_ONLN));refresh_stats();snprintf(meta[11],sizeof meta[11],"RAM:    %.0f%% used",ram);strcpy(meta[13],"// SHADOW LINK //");printf("\033[2J\033[H\n");for(int row=0;row<14;row++){printf(" %30s  \033[38;2;%s%s\033[0m\n","",row?"0;238;255m":"255;18;235m",meta[row]);}printf("\033]777;shadow-logo\a\n");g_object_unref(q);return 0;}
static void action(GtkButton*b,gpointer p){GError*e=NULL;g_spawn_command_line_async(p,&e);if(e){GtkWidget*m=gtk_message_dialog_new(NULL,0,GTK_MESSAGE_ERROR,GTK_BUTTONS_CLOSE,"%s",e->message);gtk_dialog_run(GTK_DIALOG(m));gtk_widget_destroy(m);g_error_free(e);}}
static GtkWidget*heading(const char*title,const char*subtitle){GtkWidget*row=gtk_box_new(GTK_ORIENTATION_HORIZONTAL,12);GdkPixbuf*p=gdk_pixbuf_new_from_file_at_scale(basefile("logo.png"),56,56,TRUE,NULL);if(p){gtk_box_pack_start(GTK_BOX(row),gtk_image_new_from_pixbuf(p),FALSE,FALSE,0);g_object_unref(p);}GtkWidget*col=gtk_box_new(GTK_ORIENTATION_VERTICAL,4);GtkWidget*l=gtk_label_new(NULL);gtk_label_set_text(GTK_LABEL(l),title);gtk_style_context_add_class(gtk_widget_get_style_context(l),"shadow-app-heading");gtk_widget_set_halign(l,GTK_ALIGN_START);gtk_box_pack_start(GTK_BOX(col),l,FALSE,FALSE,0);l=gtk_label_new(subtitle);gtk_widget_set_halign(l,GTK_ALIGN_START);gtk_box_pack_start(GTK_BOX(col),l,FALSE,FALSE,0);gtk_box_pack_start(GTK_BOX(row),col,TRUE,TRUE,0);return row;}
static GtkWidget*page(const char*name,const char*subtitle,GtkWidget**box){GtkWidget*w=gtk_window_new(GTK_WINDOW_TOPLEVEL);setting_window_visual(w);gtk_window_set_title(GTK_WINDOW(w),name);gtk_window_set_default_size(GTK_WINDOW(w),590,430);gtk_window_set_position(GTK_WINDOW(w),GTK_WIN_POS_CENTER);*box=gtk_box_new(GTK_ORIENTATION_VERTICAL,15);gtk_container_set_border_width(GTK_CONTAINER(*box),20);gtk_container_add(GTK_CONTAINER(w),*box);gtk_box_pack_start(GTK_BOX(*box),heading(name,subtitle),FALSE,FALSE,0);g_signal_connect(w,"destroy",G_CALLBACK(gtk_main_quit),NULL);return w;}
typedef struct {
    const char *name;
    const char *description;
    const char *command;
} ControlItem;

typedef struct {
    const char *name;
    const char *icon;
    ControlItem items[6];
} ControlSection;

static const ControlSection control_sections[] = {
    {"Appearance", "preferences-desktop-theme-symbolic", {
        {"Themes and wallpapers", "Colors, icons, wallpapers and transparency", "shadow-link --appearance"},
        {"Window manager", "Window behavior, focus and shortcuts", "xfwm4-settings"},
    }},
    {"Desktop", "user-desktop-symbolic", {
        {"Dock", "Choose, reorder and size dock shortcuts", "shadow-dock-settings"},
        {"Panel", "Configure Xfce panels and their items", "xfce4-panel --preferences"},
        {"Workspaces", "Configure virtual desktops", "xfwm4-workspace-settings"},
        {"Widgets", "Choose which status widgets appear", "shadow-link --widget-settings"},
        {"Session settings", "Manage startup applications and saved sessions", "xfce4-session-settings"},
        {"Advanced Xfce settings", "Open the full Xfce settings manager", "xfce4-settings-manager"},
    }},
    {"Devices", "preferences-desktop-peripherals-symbolic", {
        {"Display", "Resolution, monitors and orientation", "xfce4-display-settings"},
        {"Keyboard", "Layout, shortcuts and typing behavior", "xfce4-keyboard-settings"},
        {"Mouse & touchpad", "Pointer speed, buttons and scrolling", "xfce4-mouse-settings"},
        {"Audio", "Output, input and volume", "shadow-link --audio"},
        {"Bluetooth", "Adapter status and paired devices", "shadow-link --bluetooth"},
    }},
    {"Network", "network-wired-symbolic", {
        {"Connections", "Network status, Wi-Fi and connection settings", "shadow-link --network"},
    }},
    {"Privacy & Security", "security-high-symbolic", {
        {"Shadow Shield", "Firewall, VPN, Tor and privacy settings", "shadow-link --shield"},
    }},
    {"Accounts", "system-users-symbolic", {
        {"User account", "Login name, password and account picture", "shadow-account"},
        {"Login, sounds & screensaver", "Login background, session sounds and idle options", "shadowrealm-os-experience"},
    }},
    {"Software & Updates", "system-software-update-symbolic", {
        {"Software & Updates", "View installed software and manage updates", "shadow-software"},
    }},
};

static GtkWidget *control_label(const char *text)
{
    GtkWidget *label = gtk_label_new(text);
    gtk_label_set_xalign(GTK_LABEL(label), 0);
    gtk_label_set_line_wrap(GTK_LABEL(label), TRUE);
    gtk_label_set_max_width_chars(GTK_LABEL(label), 38);
    return label;
}

static GtkWidget *control_button(const ControlSection *section, const ControlItem *item)
{
    GtkWidget *button = gtk_button_new();
    GtkWidget *row = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 12);
    GtkWidget *labels = gtk_box_new(GTK_ORIENTATION_VERTICAL, 2);
    GtkWidget *description = control_label(item->description);
    gtk_style_context_add_class(gtk_widget_get_style_context(description), "dim-label");
    gtk_box_pack_start(GTK_BOX(labels), control_label(item->name), FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(labels), description, FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(row), labels, TRUE, TRUE, 0);
    gtk_box_pack_end(GTK_BOX(row), gtk_image_new_from_icon_name("go-next-symbolic",
                     GTK_ICON_SIZE_MENU), FALSE, FALSE, 0);
    gtk_container_add(GTK_CONTAINER(button), row);
    atk_object_set_name(gtk_widget_get_accessible(button), item->name);

    gchar **argv = NULL;
    if (g_shell_parse_argv(item->command, NULL, &argv, NULL)) {
        gchar *executable = g_find_program_in_path(argv[0]);
        gtk_widget_set_sensitive(button, executable != NULL);
        if (!executable)
            gtk_widget_set_tooltip_text(button, "This settings tool is unavailable.");
        g_free(executable);
        g_strfreev(argv);
    }
    g_signal_connect(button, "clicked", G_CALLBACK(action), (gpointer)item->command);
    gchar *text = g_strjoin(" ", section->name, item->name, item->description, NULL);
    g_object_set_data_full(G_OBJECT(button), "search-text", g_utf8_casefold(text, -1), g_free);
    g_free(text);
    return button;
}

static void control_search(GtkEditable *entry, gpointer data)
{
    GtkWidget *content = data;
    GtkWidget *empty = g_object_get_data(G_OBJECT(content), "no-results");
    gchar *query = g_utf8_casefold(gtk_entry_get_text(GTK_ENTRY(entry)), -1);
    g_strstrip(query);
    gboolean any = FALSE;
    GList *sections = gtk_container_get_children(GTK_CONTAINER(content));
    for (GList *section = sections; section; section = section->next) {
        if (section->data == empty)
            continue;
        gboolean visible = FALSE;
        GList *rows = gtk_container_get_children(GTK_CONTAINER(section->data));
        for (GList *row = rows; row; row = row->next) {
            const char *text = g_object_get_data(G_OBJECT(row->data), "search-text");
            if (!text)
                continue;
            gboolean match = strstr(text, query) != NULL;
            gtk_widget_set_visible(row->data, match);
            visible |= match;
        }
        g_list_free(rows);
        gtk_widget_set_visible(section->data, visible);
        any |= visible;
    }
    g_list_free(sections);
    gtk_widget_set_visible(empty, !any);
    GtkWidget *scroll = gtk_widget_get_ancestor(content, GTK_TYPE_SCROLLED_WINDOW);
    GtkAdjustment *adjustment = gtk_scrolled_window_get_vadjustment(GTK_SCROLLED_WINDOW(scroll));
    gtk_adjustment_set_value(adjustment, gtk_adjustment_get_lower(adjustment));
    g_free(query);
}

static gboolean control_search_shortcut(GtkWidget *window, GdkEventKey *event, gpointer data)
{
    (void)window;
    GdkModifierType modifiers = event->state & gtk_accelerator_get_default_mod_mask();
    if (modifiers == GDK_CONTROL_MASK && event->keyval == GDK_KEY_f) {
        gtk_widget_grab_focus(data);
        return TRUE;
    }
    return FALSE;
}

static void controls(void)
{
    GtkWidget *box;
    GtkWidget *window = page("Shadow Control Center", "Desktop and system settings", &box);
    gtk_window_set_default_size(GTK_WINDOW(window), 640, 580);
    gtk_style_context_add_class(gtk_widget_get_style_context(window), "shadow-control-center");
    GtkWidget *search = gtk_search_entry_new();
    gtk_entry_set_placeholder_text(GTK_ENTRY(search), "Search settings");
    atk_object_set_name(gtk_widget_get_accessible(search), "Search settings");
    gtk_widget_set_tooltip_text(search, "Search settings (Ctrl+F)");
    gtk_box_pack_start(GTK_BOX(box), search, FALSE, FALSE, 0);

    GtkWidget *scroll = gtk_scrolled_window_new(NULL, NULL);
    gtk_scrolled_window_set_policy(GTK_SCROLLED_WINDOW(scroll), GTK_POLICY_NEVER, GTK_POLICY_AUTOMATIC);
    gtk_scrolled_window_set_overlay_scrolling(GTK_SCROLLED_WINDOW(scroll), FALSE);
    gtk_box_pack_start(GTK_BOX(box), scroll, TRUE, TRUE, 0);
    GtkWidget *content = gtk_box_new(GTK_ORIENTATION_VERTICAL, 18);
    gtk_widget_set_margin_end(content, 8);
    gtk_container_add(GTK_CONTAINER(scroll), content);

    for (guint i = 0; i < G_N_ELEMENTS(control_sections); i++) {
        const ControlSection *section = &control_sections[i];
        GtkWidget *group = gtk_box_new(GTK_ORIENTATION_VERTICAL, 5);
        GtkWidget *header = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 8);
        gtk_box_pack_start(GTK_BOX(header), gtk_image_new_from_icon_name(section->icon,
                           GTK_ICON_SIZE_MENU), FALSE, FALSE, 0);
        GtkWidget *label = control_label(section->name);
        PangoAttrList *attrs = pango_attr_list_new();
        pango_attr_list_insert(attrs, pango_attr_weight_new(PANGO_WEIGHT_BOLD));
        gtk_label_set_attributes(GTK_LABEL(label), attrs);
        pango_attr_list_unref(attrs);
        gtk_box_pack_start(GTK_BOX(header), label, TRUE, TRUE, 0);
        gtk_box_pack_start(GTK_BOX(group), header, FALSE, FALSE, 4);
        for (guint j = 0; j < G_N_ELEMENTS(section->items) && section->items[j].name; j++)
            gtk_box_pack_start(GTK_BOX(group), control_button(section, &section->items[j]), FALSE, FALSE, 0);
        gtk_box_pack_start(GTK_BOX(content), group, FALSE, FALSE, 0);
    }

    GtkWidget *empty = control_label("No settings match your search.");
    gtk_box_pack_start(GTK_BOX(content), empty, FALSE, FALSE, 8);
    g_object_set_data(G_OBJECT(content), "no-results", empty);
    g_signal_connect(search, "search-changed", G_CALLBACK(control_search), content);
    g_signal_connect(window, "key-press-event", G_CALLBACK(control_search_shortcut), search);
    gtk_widget_show_all(window);
    gtk_widget_hide(empty);
    gtk_widget_grab_focus(search);
}
static char*shield_text(void){GString*s=g_string_new("SHADOW SHIELD / LOCAL SECURITY INVENTORY\n\n");char b[4096];FILE*f;char*nft=g_find_program_in_path("nft");g_string_append_printf(s,"Firewall tooling:  %s\n",nft?"nft present; rules need administrator verification":"nft not installed");g_free(nft);g_string_append(s,"Firewall status:   NOT VERIFIED\n\n");f=fopen("/sys/module/apparmor/parameters/enabled","r");if(f){if(fgets(b,sizeof b,f))g_string_append_printf(s,"AppArmor kernel:   %s\n",b[0]=='Y'?"enabled; policy enforcement not verified":"not enabled");fclose(f);}else g_string_append(s,"AppArmor kernel:   unavailable / not verified\n");f=fopen("/sys/fs/selinux/enforce","r");if(f){int ch=fgetc(f);fclose(f);g_string_append_printf(s,"SELinux:           %s\n",ch=='1'?"enforcing":"permissive");}else g_string_append(s,"SELinux:           not detected\n");g_string_append(s,"Disk encryption:   NOT VERIFIED\n");refresh_stats();g_string_append_printf(s,"Network interface: %s\nLocal IP address:  %s\n",iftext,iptext);g_string_append_printf(s,"VPN interface:     %s\n",vpn);g_string_append(s,"Tor readiness:     NOT VERIFIED\n\nVPN interface detection does not verify traffic routing.\nThis page reports evidence, not a security guarantee.\nNo firewall or account settings are changed here.\n");return g_string_free(s,FALSE);}
static void shield_refresh(GtkButton*b,gpointer p){char*s=shield_text();gtk_text_buffer_set_text(gtk_text_view_get_buffer(GTK_TEXT_VIEW(p)),s,-1);g_free(s);}
static void shield(void){GtkWidget*box;GtkWidget*w=page("SHADOW SHIELD","Security visibility // verified states only",&box);GtkWidget*view=gtk_text_view_new();gtk_text_view_set_editable(GTK_TEXT_VIEW(view),FALSE);gtk_text_view_set_cursor_visible(GTK_TEXT_VIEW(view),FALSE);gtk_text_view_set_monospace(GTK_TEXT_VIEW(view),TRUE);gtk_text_view_set_left_margin(GTK_TEXT_VIEW(view),12);gtk_text_view_set_top_margin(GTK_TEXT_VIEW(view),12);GtkWidget*sc=gtk_scrolled_window_new(NULL,NULL);gtk_container_add(GTK_CONTAINER(sc),view);gtk_box_pack_start(GTK_BOX(box),sc,TRUE,TRUE,0);GtkWidget*b=gtk_button_new_with_label("Refresh local checks");g_signal_connect(b,"clicked",G_CALLBACK(shield_refresh),view);gtk_box_pack_start(GTK_BOX(box),b,FALSE,FALSE,0);shield_refresh(NULL,view);gtk_widget_show_all(w);}
