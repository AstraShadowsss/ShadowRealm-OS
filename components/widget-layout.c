typedef struct {
    gboolean positioned;
    int x, y, width;
} WidgetLayout;

static WidgetLayout widget_layout[WIDGET_COUNT];
static struct {
    int index, x, y, width, applied_x, applied_y, applied_width;
    double pointer_x, pointer_y;
    gboolean resizing, changed;
} widget_drag = {.index = -1};

static char *widget_layout_path(void)
{
    return g_build_filename(g_get_user_config_dir(), "shadow-link-widget-layout.ini", NULL);
}

static void widget_layout_read(void)
{
    GKeyFile *file = g_key_file_new();
    char *path = widget_layout_path();
    g_key_file_load_from_file(file, path, G_KEY_FILE_NONE, NULL);
    for (int i = 0; i < WIDGET_COUNT; i++) {
        const char *key = widget_keys[i];
        WidgetLayout *layout = &widget_layout[i];
        layout->positioned = g_key_file_has_key(file, key, "X", NULL) &&
                             g_key_file_has_key(file, key, "Y", NULL);
        layout->x = g_key_file_get_integer(file, key, "X", NULL);
        layout->y = g_key_file_get_integer(file, key, "Y", NULL);
        layout->width = CLAMP(g_key_file_get_integer(file, key, "Width", NULL), 0, 540);
    }
    g_free(path);
    g_key_file_unref(file);
}

static void widget_layout_save(void)
{
    GKeyFile *file = g_key_file_new();
    for (int i = 0; i < WIDGET_COUNT; i++) {
        const char *key = widget_keys[i];
        const WidgetLayout *layout = &widget_layout[i];
        if (layout->positioned) {
            g_key_file_set_integer(file, key, "X", layout->x);
            g_key_file_set_integer(file, key, "Y", layout->y);
        }
        if (layout->width)
            g_key_file_set_integer(file, key, "Width", layout->width);
    }
    char *path = widget_layout_path();
    g_mkdir_with_parents(g_get_user_config_dir(), 0700);
    GError *error = NULL;
    if (!g_key_file_save_to_file(file, path, &error)) {
        g_warning("Could not save widget layout: %s", error->message);
        g_error_free(error);
    }
    g_free(path);
    g_key_file_unref(file);
}

static void widget_geometry(int index, GdkMonitor *monitor, int x, int y, int width)
{
    GdkRectangle area;
    gdk_monitor_get_workarea(monitor, &area);
    int limit = MAX(1, MIN(area.width, area.height * 270 / widget_heights[index]));
    width = CLAMP(width, 1, limit);
    int height = MAX(1, width * widget_heights[index] / 270);
    x = CLAMP(x, area.x, area.x + MAX(0, area.width - width));
    y = CLAMP(y, area.y, area.y + MAX(0, area.height - height));

    if (widget_drag.index == index) {
        widget_drag.applied_x = x;
        widget_drag.applied_y = y;
        widget_drag.applied_width = width;
    }
    GtkWindow *window = GTK_WINDOW(cardwindows[index]);
    widget_scale[index] = width / 270.;
    gtk_widget_set_size_request(cards[index], width, height);
    gtk_window_resize(window, width, height);
    gtk_window_move(window, x, y);
}

static void reflow_widgets(void)
{
    GdkDisplay *display = gdk_display_get_default();
    GdkMonitor *primary = gdk_display_get_primary_monitor(display);
    if (!primary)
        primary = gdk_display_get_monitor(display, 0);
    if (!primary)
        return;
    GdkRectangle area;
    gdk_monitor_get_workarea(primary, &area);
    int total = 0;
    for (int i = 0; i < WIDGET_COUNT; i++) {
        if (widget_enabled(i))
            total += widget_heights[i] + 12;
    }
    double size = CLAMP((area.height - 85) / 685., .68, 1.2) *
                  CLAMP(widget_integer("ScalePercent", 100), 70, 120) / 100.;
    if (total)
        size = MIN(size, MAX(1, area.height - 30) / (double) total);
    int margin = CLAMP(widget_integer("RightMargin", 12), 0, 150);
    int y = area.y + 20;
    for (int i = 0; i < WIDGET_COUNT; i++) {
        if (!widget_enabled(i)) {
            if (cardwindows[i])
                gtk_widget_hide(cardwindows[i]);
            continue;
        }
        int slot_y = y;
        y += (int)((widget_heights[i] + 12) * size);
        if (!cardwindows[i] || i == widget_drag.index)
            continue;
        WidgetLayout *layout = &widget_layout[i];
        int width = layout->width > 0 ? layout->width : MAX(1, (int)(270 * size));
        if (layout->positioned) {
            GdkMonitor *monitor = gdk_display_get_monitor_at_point(display, layout->x, layout->y);
            widget_geometry(i, monitor ? monitor : primary, layout->x, layout->y, width);
        } else {
            widget_geometry(i, primary, area.x + area.width - width - margin, slot_y, width);
        }
        gtk_widget_show(cardwindows[i]);
    }
}

static void widget_reset_layout(GtkMenuItem *item, gpointer data)
{
    (void)item;
    widget_layout[GPOINTER_TO_INT(data)] = (WidgetLayout){0};
    widget_layout_save();
    reflow_widgets();
}

static void widget_open_preferences(GtkMenuItem *item, gpointer data)
{
    (void)item;
    (void)data;
    g_spawn_command_line_async("shadowrealm-os-desktop widget-settings", NULL);
}

static gboolean widget_resize_hit(GtkWidget *card, double x, double y)
{
    return x >= gtk_widget_get_allocated_width(card) - 23 &&
           y >= gtk_widget_get_allocated_height(card) - 23;
}

static gboolean widget_button_press(GtkWidget *card, GdkEventButton *event, gpointer data)
{
    int index = GPOINTER_TO_INT(data);
    if (event->button == 3) {
        GtkWidget *menu = gtk_menu_new();
        gtk_menu_attach_to_widget(GTK_MENU(menu), card, NULL);
        GtkWidget *reset = gtk_menu_item_new_with_label("Reset position and size");
        GtkWidget *settings = gtk_menu_item_new_with_label("Widget settings");
        gtk_menu_shell_append(GTK_MENU_SHELL(menu), reset);
        gtk_menu_shell_append(GTK_MENU_SHELL(menu), settings);
        g_signal_connect(reset, "activate", G_CALLBACK(widget_reset_layout), data);
        g_signal_connect(settings, "activate", G_CALLBACK(widget_open_preferences), NULL);
        g_signal_connect_swapped(menu, "selection-done", G_CALLBACK(gtk_widget_destroy), menu);
        gtk_widget_show_all(menu);
        gtk_menu_popup_at_pointer(GTK_MENU(menu), (GdkEvent *)event);
        return TRUE;
    }
    if (event->button != 1 || event->type != GDK_BUTTON_PRESS || widget_drag.index >= 0)
        return FALSE;
    gboolean resize = widget_resize_hit(card, event->x, event->y);
    if (!resize && event->y > 38 * widget_scale[index]) {
        if (index != WIDGET_NOTES)
            return FALSE;
        edit_widget_notes();
        return TRUE;
    }
    widget_drag.index = index;
    gtk_window_get_position(GTK_WINDOW(cardwindows[index]), &widget_drag.x, &widget_drag.y);
    widget_drag.width = gtk_widget_get_allocated_width(card);
    widget_drag.pointer_x = event->x_root;
    widget_drag.pointer_y = event->y_root;
    widget_drag.resizing = resize;
    widget_drag.changed = FALSE;
    return TRUE;
}

static gboolean widget_motion(GtkWidget *card, GdkEventMotion *event, gpointer data)
{
    int index = GPOINTER_TO_INT(data);
    if (widget_drag.index != index) {
        const char *name = widget_resize_hit(card, event->x, event->y) ? "nwse-resize" :
                           event->y <= 38 * widget_scale[index] ? "move" :
                           index == WIDGET_NOTES ? "pointer" : NULL;
        GdkCursor *cursor = name ? gdk_cursor_new_from_name(gtk_widget_get_display(card), name) : NULL;
        gdk_window_set_cursor(gtk_widget_get_window(card), cursor);
        g_clear_object(&cursor);
        return FALSE;
    }
    int dx = (int)(event->x_root - widget_drag.pointer_x);
    int dy = (int)(event->y_root - widget_drag.pointer_y);
    if (!widget_drag.changed && ABS(dx) < 3 && ABS(dy) < 3)
        return TRUE;
    GdkDisplay *display = gtk_widget_get_display(card);
    GdkMonitor *monitor = gdk_display_get_monitor_at_point(display, event->x_root, event->y_root);
    int x = widget_drag.x, y = widget_drag.y, width = widget_drag.width;
    if (widget_drag.resizing) {
        int vertical = dy * 270 / widget_heights[index];
        int delta = ABS(dx) >= ABS(vertical) ? dx : vertical;
        width = CLAMP(widget_drag.width + delta, 165, 540);
        monitor = gdk_display_get_monitor_at_point(display, x, y);
    } else {
        x += dx;
        y += dy;
    }
    if (monitor) {
        widget_geometry(index, monitor, x, y, width);
        widget_drag.changed = TRUE;
    }
    return TRUE;
}

static gboolean widget_button_release(GtkWidget *card, GdkEventButton *event, gpointer data)
{
    int index = GPOINTER_TO_INT(data);
    if (event->button != 1 || widget_drag.index != index)
        return FALSE;
    if (widget_drag.changed) {
        WidgetLayout *layout = &widget_layout[index];
        layout->positioned = TRUE;
        layout->x = widget_drag.applied_x;
        layout->y = widget_drag.applied_y;
        layout->width = widget_drag.applied_width;
        widget_layout_save();
    }
    widget_drag.index = -1;
    return TRUE;
}

static gboolean widget_grab_broken(GtkWidget *card, GdkEventGrabBroken *event, gpointer data)
{
    (void)card;
    (void)event;
    if (widget_drag.index == GPOINTER_TO_INT(data)) {
        widget_drag.index = -1;
        reflow_widgets();
    }
    return FALSE;
}

static void widget_input(GtkWidget *card, int index)
{
    gpointer data = GINT_TO_POINTER(index);
    gtk_widget_add_events(card, GDK_BUTTON_PRESS_MASK | GDK_BUTTON_RELEASE_MASK |
                                 GDK_POINTER_MOTION_MASK);
    gtk_widget_set_tooltip_text(card, index == WIDGET_NOTES ?
        "Click to edit notes. Drag the header to move or the corner to resize." :
        "Drag the header to move or the bottom-right corner to resize.");
    g_signal_connect(card, "button-press-event", G_CALLBACK(widget_button_press), data);
    g_signal_connect(card, "button-release-event", G_CALLBACK(widget_button_release), data);
    g_signal_connect(card, "motion-notify-event", G_CALLBACK(widget_motion), data);
    g_signal_connect(card, "grab-broken-event", G_CALLBACK(widget_grab_broken), data);
}
