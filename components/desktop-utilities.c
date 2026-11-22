static GtkWidget*calc_entry,*calc_result;
static const char*exprp;static gboolean exprerr;
static void spaces(void){while(g_ascii_isspace(*exprp))exprp++;}
static double expression(void);
static double atom(void){spaces();if(*exprp=='+'){exprp++;return atom();}if(*exprp=='-'){exprp++;return -atom();}if(*exprp=='('){exprp++;double v=expression();spaces();if(*exprp==')')exprp++;else exprerr=TRUE;return v;}char*end;double v=g_ascii_strtod(exprp,&end);if(end==exprp){exprerr=TRUE;return 0;}exprp=end;return v;}
static double power_expr(void){double v=atom();spaces();if(*exprp=='^'){exprp++;v=pow(v,power_expr());}return v;}
static double product(void){double v=power_expr();for(;;){spaces();char op=*exprp;if(op!='*'&&op!='/')break;exprp++;double n=power_expr();if(op=='*')v*=n;else if(n==0)exprerr=TRUE;else v/=n;}return v;}
static double expression(void){double v=product();for(;;){spaces();char op=*exprp;if(op!='+'&&op!='-')break;exprp++;double n=product();v=op=='+'?v+n:v-n;}return v;}
static gboolean calculate(const char*text,double*out){exprp=text;exprerr=FALSE;*out=expression();spaces();return !exprerr&&!*exprp&&isfinite(*out);}
static void calc_eval(GtkWidget*w,gpointer data){double v;char s[128];if(calculate(gtk_entry_get_text(GTK_ENTRY(calc_entry)),&v))snprintf(s,sizeof s,"%.12g",v);else strcpy(s,"Check the expression (or division by zero)");gtk_label_set_text(GTK_LABEL(calc_result),s);}
static void calc_key(GtkButton*b,gpointer p){const char*k=p;if(!strcmp(k,"=")){calc_eval(NULL,NULL);return;}if(!strcmp(k,"C")){gtk_entry_set_text(GTK_ENTRY(calc_entry),"");gtk_label_set_text(GTK_LABEL(calc_result),"0");return;}int pos=gtk_editable_get_position(GTK_EDITABLE(calc_entry));gtk_editable_insert_text(GTK_EDITABLE(calc_entry),k,-1,&pos);gtk_editable_set_position(GTK_EDITABLE(calc_entry),pos);gtk_widget_grab_focus(calc_entry);}
static void calculator(void){GtkWidget*box;GtkWidget*w=page("SHADOW CALCULATOR","Everyday arithmetic // + − × ÷ ( ) powers",&box);gtk_window_set_default_size(GTK_WINDOW(w),360,470);calc_entry=gtk_entry_new();gtk_box_pack_start(GTK_BOX(box),calc_entry,FALSE,FALSE,0);g_signal_connect(calc_entry,"activate",G_CALLBACK(calc_eval),NULL);calc_result=gtk_label_new("0");gtk_label_set_xalign(GTK_LABEL(calc_result),1);gtk_box_pack_start(GTK_BOX(box),calc_result,FALSE,FALSE,4);GtkWidget*grid=gtk_grid_new();gtk_grid_set_row_spacing(GTK_GRID(grid),5);gtk_grid_set_column_spacing(GTK_GRID(grid),5);const char*k[]={"C","(",")","/","7","8","9","*","4","5","6","-","1","2","3","+","0",".","^","="};for(int i=0;i<20;i++){GtkWidget*b=gtk_button_new_with_label(k[i]);gtk_widget_set_hexpand(b,TRUE);gtk_widget_set_vexpand(b,TRUE);g_signal_connect(b,"clicked",G_CALLBACK(calc_key),(gpointer)k[i]);gtk_grid_attach(GTK_GRID(grid),b,i%4,i/4,1,1);}gtk_box_pack_start(GTK_BOX(box),grid,TRUE,TRUE,0);gtk_widget_show_all(w);gtk_widget_grab_focus(calc_entry);}
static GtkWidget*calendar_widget,*calendar_note,*calendar_date;
static char*note_path(void){guint y,m,d;gtk_calendar_get_date(GTK_CALENDAR(calendar_widget),&y,&m,&d);return g_strdup_printf("%s/.local/share/shadow-link/calendar/%04u-%02u-%02u.txt",g_get_home_dir(),y,m+1,d);}
static void calendar_pick(GtkCalendar*c,gpointer p){guint y,m,d;gtk_calendar_get_date(c,&y,&m,&d);char date[64];snprintf(date,sizeof date,"%04u-%02u-%02u / local note",y,m+1,d);gtk_label_set_text(GTK_LABEL(calendar_date),date);char*path=note_path(),*text=NULL;g_file_get_contents(path,&text,NULL,NULL);gtk_text_buffer_set_text(gtk_text_view_get_buffer(GTK_TEXT_VIEW(calendar_note)),text?text:"",-1);g_free(text);g_free(path);}
static void calendar_save(GtkButton*b,gpointer p){char*dir=g_strdup_printf("%s/.local/share/shadow-link/calendar",g_get_home_dir());g_mkdir_with_parents(dir,0700);g_free(dir);GtkTextBuffer*buf=gtk_text_view_get_buffer(GTK_TEXT_VIEW(calendar_note));GtkTextIter a,z;gtk_text_buffer_get_bounds(buf,&a,&z);char*text=gtk_text_buffer_get_text(buf,&a,&z,FALSE),*path=note_path();GError*e=NULL;if(!g_file_set_contents(path,text,-1,&e)){gtk_label_set_text(GTK_LABEL(calendar_date),e->message);g_error_free(e);}else gtk_label_set_text(GTK_LABEL(calendar_date),"Note saved locally");g_free(path);g_free(text);}
static void calendar_page(void){GtkWidget*box;GtkWidget*w=page("SHADOW CALENDAR","Local calendar and date notes",&box);calendar_widget=gtk_calendar_new();gtk_calendar_set_display_options(GTK_CALENDAR(calendar_widget),GTK_CALENDAR_SHOW_HEADING|GTK_CALENDAR_SHOW_DAY_NAMES|GTK_CALENDAR_SHOW_WEEK_NUMBERS);gtk_box_pack_start(GTK_BOX(box),calendar_widget,FALSE,FALSE,0);calendar_date=gtk_label_new("");gtk_box_pack_start(GTK_BOX(box),calendar_date,FALSE,FALSE,0);calendar_note=gtk_text_view_new();gtk_text_view_set_wrap_mode(GTK_TEXT_VIEW(calendar_note),GTK_WRAP_WORD_CHAR);GtkWidget*sc=gtk_scrolled_window_new(NULL,NULL);gtk_widget_set_size_request(sc,-1,100);gtk_container_add(GTK_CONTAINER(sc),calendar_note);gtk_box_pack_start(GTK_BOX(box),sc,TRUE,TRUE,0);GtkWidget*b=gtk_button_new_with_label("Save date note");g_signal_connect(b,"clicked",G_CALLBACK(calendar_save),NULL);gtk_box_pack_start(GTK_BOX(box),b,FALSE,FALSE,0);g_signal_connect(calendar_widget,"day-selected",G_CALLBACK(calendar_pick),NULL);calendar_pick(GTK_CALENDAR(calendar_widget),NULL);gtk_widget_show_all(w);}
static GtkWidget*clock_time,*clock_date,*clock_elapsed;static gint64 clock_started;static double clock_accumulated;static gboolean clock_running;
static gboolean clock_tick(gpointer p){GDateTime*now=g_date_time_new_now_local();char*t=g_date_time_format(now,"%I:%M:%S %p"),*date=g_date_time_format(now,"%A, %d %B %Y  ·  %Z");gtk_label_set_text(GTK_LABEL(clock_time),t);gtk_label_set_text(GTK_LABEL(clock_date),date);double sec=clock_accumulated+(clock_running?(g_get_monotonic_time()-clock_started)/1000000.:0);char elapsed[80];snprintf(elapsed,sizeof elapsed,"Stopwatch  %02d:%02d:%02d",(int)sec/3600,(int)sec/60%60,(int)sec%60);gtk_label_set_text(GTK_LABEL(clock_elapsed),elapsed);g_free(t);g_free(date);g_date_time_unref(now);return G_SOURCE_CONTINUE;}
static void clock_toggle(GtkButton*b,gpointer p){if(clock_running)clock_accumulated+=(g_get_monotonic_time()-clock_started)/1000000.;else clock_started=g_get_monotonic_time();clock_running=!clock_running;gtk_button_set_label(b,clock_running?"Pause stopwatch":"Start stopwatch");}
static void clock_reset(GtkButton*b,gpointer p){clock_accumulated=0;clock_started=g_get_monotonic_time();clock_tick(NULL);}
static void clock_alarms(GtkButton*b,gpointer d){(void)b;(void)d;g_spawn_command_line_async("gnome-clocks",NULL);}
static void clock_page(void){GtkWidget*box;GtkWidget*w=page("SHADOW CLOCK","Local time // live clock and stopwatch",&box);gtk_window_set_default_size(GTK_WINDOW(w),470,300);clock_time=gtk_label_new("");gtk_style_context_add_class(gtk_widget_get_style_context(clock_time),"shadow-clock-time");clock_date=gtk_label_new("");clock_elapsed=gtk_label_new("");gtk_box_pack_start(GTK_BOX(box),clock_time,TRUE,TRUE,0);gtk_box_pack_start(GTK_BOX(box),clock_date,FALSE,FALSE,0);gtk_box_pack_start(GTK_BOX(box),clock_elapsed,FALSE,FALSE,0);GtkWidget*row=gtk_box_new(GTK_ORIENTATION_HORIZONTAL,8);GtkWidget*b=gtk_button_new_with_label("Start stopwatch");g_signal_connect(b,"clicked",G_CALLBACK(clock_toggle),NULL);gtk_box_pack_start(GTK_BOX(row),b,TRUE,TRUE,0);b=gtk_button_new_with_label("Reset");g_signal_connect(b,"clicked",G_CALLBACK(clock_reset),NULL);gtk_box_pack_start(GTK_BOX(row),b,TRUE,TRUE,0);gtk_box_pack_start(GTK_BOX(box),row,FALSE,FALSE,0);b=gtk_button_new_with_label("Alarms & Timers…");g_signal_connect(b,"clicked",G_CALLBACK(clock_alarms),NULL);gtk_box_pack_start(GTK_BOX(box),b,FALSE,FALSE,0);clock_tick(NULL);g_timeout_add(250,clock_tick,NULL);gtk_widget_show_all(w);}
static GKeyFile *widget_config;
static char*widget_config_path(void){return g_build_filename(g_get_user_config_dir(),"shadow-link-widgets.ini",NULL);}
static void widgets_read(void)
{
    if (widget_config)
        g_key_file_unref(widget_config);
    widget_config = g_key_file_new();
    char *path = widget_config_path();
    g_key_file_load_from_file(widget_config, path, G_KEY_FILE_NONE, NULL);
    g_free(path);
    for (int i = 0; i < WIDGET_COUNT; i++) {
        for (int role = 0; role < WIDGET_COLOR_COUNT; role++) {
            char *value = g_key_file_get_string(widget_config, widget_color_keys[role], widget_keys[i], NULL);
            widget_has_color[i][role] = value && gdk_rgba_parse(&widget_colors[i][role], value);
            g_free(value);
        }
        GError *error = NULL;
        int opacity = g_key_file_get_integer(widget_config, "Opacity", widget_keys[i], &error);
        widget_opacity[i] = error ? -1 : CLAMP(opacity, 0, 100);
        g_clear_error(&error);
    }
}

static gboolean widget_enabled(int i)
{
    GError *error = NULL;
    const char *key = i == WIDGET_CLOCK ? "Clock" : widget_keys[i];
    gboolean enabled = g_key_file_get_boolean(widget_config, "Widgets", key, &error);
    if (error) {
        g_error_free(error);
        if (i == WIDGET_CLOCK || i == WIDGET_CALENDAR)
            return g_key_file_get_boolean(widget_config, "Widgets", widget_keys[WIDGET_CLOCK], NULL);
        return i < WIDGET_CLOCK;
    }
    return enabled;
}
static int widget_integer(const char*key,int fallback){return g_key_file_has_key(widget_config,"Widgets",key,NULL)?g_key_file_get_integer(widget_config,"Widgets",key,NULL):fallback;}
static void widgets_save(void){gsize n;char*s=g_key_file_to_data(widget_config,&n,NULL),*p=widget_config_path();g_file_set_contents(p,s,n,NULL);g_free(p);g_free(s);}
static void widget_toggle(GtkToggleButton*b,gpointer p){widgets_read();g_key_file_set_boolean(widget_config,"Widgets",p,gtk_toggle_button_get_active(b));widgets_save();}
static void widget_spin(GtkSpinButton*b,gpointer p){g_key_file_set_integer(widget_config,"Widgets",p,gtk_spin_button_get_value_as_int(b));widgets_save();}
typedef struct {
    int index, role;
    GtkWidget *picker;
} WidgetColorSetting;

static void widget_choose_color(GtkColorButton *button, gpointer data)
{
    WidgetColorSetting *setting = data;
    GdkRGBA color;
    gtk_color_chooser_get_rgba(GTK_COLOR_CHOOSER(button), &color);
    gchar *value = gdk_rgba_to_string(&color);
    widgets_read();
    g_key_file_set_string(widget_config, widget_color_keys[setting->role], widget_keys[setting->index], value);
    g_free(value);
    widgets_save();
}

static void widget_reset_color(GtkButton *button, gpointer data)
{
    (void)button;
    WidgetColorSetting *setting = data;
    GdkRGBA unset = {0.5, 0.5, 0.5, 1};
    gtk_color_chooser_set_rgba(GTK_COLOR_CHOOSER(setting->picker), &unset);
    widgets_read();
    g_key_file_remove_key(widget_config, widget_color_keys[setting->role], widget_keys[setting->index], NULL);
    widgets_save();
}

static void widget_color_dialog(GtkButton *button, gpointer data)
{
    int index = GPOINTER_TO_INT(data);
    GtkWindow *parent = GTK_WINDOW(gtk_widget_get_toplevel(GTK_WIDGET(button)));
    GtkWidget *dialog = gtk_dialog_new_with_buttons(widget_names[index], parent,
        GTK_DIALOG_MODAL | GTK_DIALOG_DESTROY_WITH_PARENT, "Done", GTK_RESPONSE_CLOSE, NULL);
    GtkWidget *grid = gtk_grid_new();
    gtk_container_set_border_width(GTK_CONTAINER(grid), 16);
    gtk_grid_set_row_spacing(GTK_GRID(grid), 10);
    gtk_grid_set_column_spacing(GTK_GRID(grid), 12);
    gtk_container_add(GTK_CONTAINER(gtk_dialog_get_content_area(GTK_DIALOG(dialog))), grid);
    const char *labels[] = {"Border", "Text and numbers", "Usage bars", "History graph"};
    WidgetColorSetting settings[WIDGET_COLOR_COUNT];
    widgets_read();
    for (int role = 0; role < WIDGET_COLOR_COUNT; role++) {
        if (role == WIDGET_BAR && index != 0)
            continue;
        GdkRGBA neutral = {0.5, 0.5, 0.5, 1};
        GtkWidget *picker = gtk_color_button_new_with_rgba(
            widget_has_color[index][role] ? &widget_colors[index][role] : &neutral);
        gtk_color_button_set_title(GTK_COLOR_BUTTON(picker), labels[role]);
        atk_object_set_name(gtk_widget_get_accessible(picker), labels[role]);
        settings[role] = (WidgetColorSetting){index, role, picker};
        GtkWidget *label = gtk_label_new(labels[role]);
        gtk_label_set_xalign(GTK_LABEL(label), 0);
        gtk_grid_attach(GTK_GRID(grid), label, 0, role, 1, 1);
        gtk_grid_attach(GTK_GRID(grid), picker, 1, role, 1, 1);
        GtkWidget *reset = gtk_button_new_with_label("Use theme");
        gtk_grid_attach(GTK_GRID(grid), reset, 2, role, 1, 1);
        g_signal_connect(picker, "color-set", G_CALLBACK(widget_choose_color), &settings[role]);
        g_signal_connect(reset, "clicked", G_CALLBACK(widget_reset_color), &settings[role]);
    }
    gtk_widget_show_all(dialog);
    gtk_dialog_run(GTK_DIALOG(dialog));
    gtk_widget_destroy(dialog);
}

static void widget_set_opacity(GtkSpinButton *button, gpointer key)
{
    int opacity = gtk_spin_button_get_value_as_int(button);
    widgets_read();
    if (opacity < 0)
        g_key_file_remove_key(widget_config, "Opacity", key, NULL);
    else
        g_key_file_set_integer(widget_config, "Opacity", key, opacity);
    widgets_save();
}

static gboolean widget_opacity_output(GtkSpinButton *button, gpointer unused)
{
    (void)unused;
    if (gtk_spin_button_get_value_as_int(button) < 0) {
        gtk_entry_set_text(GTK_ENTRY(button), "Theme");
        return TRUE;
    }
    return FALSE;
}

static gint widget_opacity_input(GtkSpinButton *button, gdouble *value, gpointer unused)
{
    (void)unused;
    if (!g_ascii_strcasecmp(gtk_entry_get_text(GTK_ENTRY(button)), "Theme")) {
        *value = -1;
        return TRUE;
    }
    return FALSE;
}

static void widget_professional(GtkToggleButton *button, gpointer unused)
{
    (void)unused;
    widget_toggle(button, "Professional");
    g_spawn_command_line_async("shadowrealm-os-desktop sync-widgets", NULL);
}

static void update_weather_from_config(void)
{
    gchar *unit = g_key_file_get_string(widget_config, "Weather", "Unit", NULL);
    weather_fahrenheit = g_strcmp0(unit, "C") != 0;
    g_free(unit);
    GError *latitude_error = NULL, *longitude_error = NULL;
    double latitude = g_key_file_get_double(widget_config, "Weather", "Latitude", &latitude_error);
    double longitude = g_key_file_get_double(widget_config, "Weather", "Longitude", &longitude_error);
    weather_update(widget_enabled(WIDGET_WEATHER) && !latitude_error && !longitude_error,
                   latitude, longitude);
    g_clear_error(&latitude_error);
    g_clear_error(&longitude_error);
}

static gboolean weather_coordinate(GtkWidget *entry, double limit, double *result)
{
    const char *input = gtk_entry_get_text(GTK_ENTRY(entry));
    char *end = NULL;
    *result = g_ascii_strtod(input, &end);
    return end != input && !*end && isfinite(*result) && fabs(*result) <= limit;
}

static void weather_settings(GtkButton *button, gpointer unused)
{
    (void)unused;
    GtkWindow *parent = GTK_WINDOW(gtk_widget_get_toplevel(GTK_WIDGET(button)));
    GtkWidget *dialog = gtk_dialog_new_with_buttons("Weather location & units", parent, GTK_DIALOG_MODAL,
                                                   "Cancel", GTK_RESPONSE_CANCEL,
                                                   "Save location", GTK_RESPONSE_ACCEPT, NULL);
    GtkWidget *content = gtk_dialog_get_content_area(GTK_DIALOG(dialog));
    gtk_container_set_border_width(GTK_CONTAINER(content), 14);
    GtkWidget *notice = gtk_label_new("When the Weather widget is enabled, rounded coordinates are sent to MET Norway for the forecast. Enter a nearby location using latitude and longitude.");
    gtk_label_set_line_wrap(GTK_LABEL(notice), TRUE);
    gtk_label_set_max_width_chars(GTK_LABEL(notice), 48);
    gtk_box_pack_start(GTK_BOX(content), notice, FALSE, FALSE, 8);
    GtkWidget *lat = gtk_entry_new(), *lon = gtk_entry_new();
    gtk_entry_set_placeholder_text(GTK_ENTRY(lat), "Latitude, for example 59.91");
    gtk_entry_set_placeholder_text(GTK_ENTRY(lon), "Longitude, for example 10.75");
    atk_object_set_name(gtk_widget_get_accessible(lat), "Latitude");
    atk_object_set_name(gtk_widget_get_accessible(lon), "Longitude");
    widgets_read();
    GtkWidget *units = gtk_combo_box_text_new();
    gtk_combo_box_text_append(GTK_COMBO_BOX_TEXT(units), "F", "Fahrenheit (°F)");
    gtk_combo_box_text_append(GTK_COMBO_BOX_TEXT(units), "C", "Celsius (°C)");
    gchar *unit = g_key_file_get_string(widget_config, "Weather", "Unit", NULL);
    gtk_combo_box_set_active_id(GTK_COMBO_BOX(units), g_strcmp0(unit, "C") == 0 ? "C" : "F");
    g_free(unit);
    atk_object_set_name(gtk_widget_get_accessible(units), "Temperature unit");
    gtk_box_pack_start(GTK_BOX(content), units, FALSE, FALSE, 4);
    const char *keys[] = {"Latitude", "Longitude"};
    GtkWidget *fields[] = {lat, lon};
    for (int i = 0; i < 2; i++) {
        gchar *value = g_key_file_get_value(widget_config, "Weather", keys[i], NULL);
        if (value) {
            gchar formatted[G_ASCII_DTOSTR_BUF_SIZE];
            g_ascii_formatd(formatted, sizeof formatted, "%.2f", g_ascii_strtod(value, NULL));
            gtk_entry_set_text(GTK_ENTRY(fields[i]), formatted);
        }
        g_free(value);
        gtk_box_pack_start(GTK_BOX(content), fields[i], FALSE, FALSE, 4);
    }
    GtkWidget *status = gtk_label_new("");
    gtk_box_pack_start(GTK_BOX(content), status, FALSE, FALSE, 4);
    gtk_widget_show_all(dialog);
    while (gtk_dialog_run(GTK_DIALOG(dialog)) == GTK_RESPONSE_ACCEPT) {
        double latitude, longitude;
        if (!weather_coordinate(lat, 90, &latitude) || !weather_coordinate(lon, 180, &longitude)) {
            gtk_label_set_text(GTK_LABEL(status), "Enter valid latitude and longitude.");
            continue;
        }
        widgets_read();
        g_key_file_set_double(widget_config, "Weather", "Latitude", latitude);
        g_key_file_set_double(widget_config, "Weather", "Longitude", longitude);
        g_key_file_set_string(widget_config, "Weather", "Unit",
                              gtk_combo_box_get_active_id(GTK_COMBO_BOX(units)));
        widgets_save();
        break;
    }
    gtk_widget_destroy(dialog);
}

static void widget_settings(void)
{
    widgets_read();
    GtkWidget *box;
    GtkWidget *window = page("Shadow Widgets", "Choose which desktop widgets appear and how they look", &box);
    gtk_window_set_default_size(GTK_WINDOW(window), 680, 640);
    GtkWidget *weather_controls = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 12);
    GtkWidget *weather_enabled = gtk_check_button_new_with_label("Show Weather");
    gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(weather_enabled), widget_enabled(WIDGET_WEATHER));
    g_signal_connect(weather_enabled, "toggled", G_CALLBACK(widget_toggle), (gpointer)widget_keys[WIDGET_WEATHER]);
    GtkWidget *location = gtk_button_new_with_label("Weather location & units…");
    g_signal_connect(location, "clicked", G_CALLBACK(weather_settings), NULL);
    gtk_box_pack_start(GTK_BOX(weather_controls), weather_enabled, FALSE, FALSE, 0);
    gtk_box_pack_end(GTK_BOX(weather_controls), location, FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(box), weather_controls, FALSE, FALSE, 0);
    GtkWidget *scroll = gtk_scrolled_window_new(NULL, NULL);
    gtk_scrolled_window_set_policy(GTK_SCROLLED_WINDOW(scroll), GTK_POLICY_NEVER, GTK_POLICY_AUTOMATIC);
    gtk_box_pack_start(GTK_BOX(box), scroll, TRUE, TRUE, 0);
    GtkWidget *grid = gtk_grid_new();
    gtk_grid_set_row_spacing(GTK_GRID(grid), 12);
    gtk_grid_set_column_spacing(GTK_GRID(grid), 10);
    gtk_container_add(GTK_CONTAINER(scroll), grid);
    gtk_grid_attach(GTK_GRID(grid), gtk_label_new("Widget"), 0, 0, 1, 1);
    gtk_grid_attach(GTK_GRID(grid), gtk_label_new("Colors"), 1, 0, 2, 1);
    gtk_grid_attach(GTK_GRID(grid), gtk_label_new("Background (%)"), 3, 0, 1, 1);
    for (int i = 0; i < WIDGET_COUNT; i++) {
        const char *key = widget_keys[i];
        GtkWidget *name;
        if (i == WIDGET_WEATHER) {
            name = gtk_label_new(widget_names[i]);
            gtk_label_set_xalign(GTK_LABEL(name), 0);
        } else {
            name = gtk_check_button_new_with_label(widget_names[i]);
            gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(name), widget_enabled(i));
            const char *visibility_key = i == WIDGET_CLOCK ? "Clock" : key;
            g_signal_connect(name, "toggled", G_CALLBACK(widget_toggle), (gpointer)visibility_key);
        }
        gtk_widget_set_hexpand(name, TRUE);
        gtk_grid_attach(GTK_GRID(grid), name, 0, i + 1, 1, 1);

        GtkWidget *colors = gtk_button_new_with_label("Edit colors…");
        g_signal_connect(colors, "clicked", G_CALLBACK(widget_color_dialog), GINT_TO_POINTER(i));
        gtk_grid_attach(GTK_GRID(grid), colors, 1, i + 1, 2, 1);

        GtkWidget *opacity = gtk_spin_button_new_with_range(-1, 100, 1);
        gtk_spin_button_set_numeric(GTK_SPIN_BUTTON(opacity), FALSE);
        gtk_entry_set_width_chars(GTK_ENTRY(opacity), 6);
        g_signal_connect(opacity, "output", G_CALLBACK(widget_opacity_output), NULL);
        g_signal_connect(opacity, "input", G_CALLBACK(widget_opacity_input), NULL);
        gtk_spin_button_set_value(GTK_SPIN_BUTTON(opacity), widget_opacity[i]);
        gtk_widget_set_tooltip_text(opacity, "Theme follows the shared background opacity from Appearance");
        atk_object_set_name(gtk_widget_get_accessible(opacity), widget_names[i]);
        g_signal_connect(opacity, "value-changed", G_CALLBACK(widget_set_opacity), (gpointer)key);
        gtk_grid_attach(GTK_GRID(grid), opacity, 3, i + 1, 1, 1);
    }
    GtkWidget *note = gtk_label_new("Theme uses the shared background opacity from Appearance.");
    gtk_label_set_xalign(GTK_LABEL(note), 0);
    gtk_grid_attach(GTK_GRID(grid), note, 0, WIDGET_COUNT + 1, 4, 1);
    GtkWidget *layout_help = gtk_label_new("Drag a widget by its header or resize from its bottom-right corner. Right-click it to reset.");
    gtk_label_set_xalign(GTK_LABEL(layout_help), 0);
    gtk_label_set_line_wrap(GTK_LABEL(layout_help), TRUE);
    gtk_grid_attach(GTK_GRID(grid), layout_help, 0, WIDGET_COUNT + 2, 4, 1);
    const char *labels[] = {"Refresh interval (seconds)", "Widget size (%)", "Right margin (pixels)"};
    const char *keys[] = {"RefreshSeconds", "ScalePercent", "RightMargin"};
    const int low[] = {1, 70, 0}, high[] = {15, 120, 150}, defaults[] = {2, 100, 12};
    for (int i = 0; i < 3; i++) {
        GtkWidget *label = gtk_label_new(labels[i]);
        gtk_label_set_xalign(GTK_LABEL(label), 0);
        GtkWidget *spin = gtk_spin_button_new_with_range(low[i], high[i], 1);
        gtk_spin_button_set_value(GTK_SPIN_BUTTON(spin), widget_integer(keys[i], defaults[i]));
        gtk_label_set_mnemonic_widget(GTK_LABEL(label), spin);
        g_signal_connect(spin, "value-changed", G_CALLBACK(widget_spin), (gpointer)keys[i]);
        gtk_grid_attach(GTK_GRID(grid), label, 0, WIDGET_COUNT + i + 3, 3, 1);
        gtk_grid_attach(GTK_GRID(grid), spin, 3, WIDGET_COUNT + i + 3, 1, 1);
    }
    GtkWidget *professional = gtk_check_button_new_with_label("Show widgets in the Professional theme");
    gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(professional),
                                 g_key_file_get_boolean(widget_config, "Widgets", "Professional", NULL));
    g_signal_connect(professional, "toggled", G_CALLBACK(widget_professional), NULL);
    gtk_grid_attach(GTK_GRID(grid), professional, 0, WIDGET_COUNT + 6, 4, 1);
    gtk_widget_show_all(window);
}
