static char *widget_notes_path(void)
{
    return g_build_filename(g_get_user_data_dir(), "shadowrealm-os", "widget-notes.txt", NULL);
}

static char *widget_notes_text(void)
{
    char *path = widget_notes_path();
    char *text = NULL;
    g_file_get_contents(path, &text, NULL, NULL);
    g_free(path);
    if (text && !g_utf8_validate(text, -1, NULL))
        g_clear_pointer(&text, g_free);
    return text;
}

static void draw_widget_notes(cairo_t *canvas)
{
    char *text = widget_notes_text();
    PangoLayout *layout = pango_cairo_create_layout(canvas);
    PangoFontDescription *font = pango_font_description_from_string("Sans 10");
    pango_layout_set_font_description(layout, font);
    pango_font_description_free(font);
    pango_layout_set_width(layout, 238 * PANGO_SCALE);
    pango_layout_set_height(layout, 100 * PANGO_SCALE);
    pango_layout_set_wrap(layout, PANGO_WRAP_WORD_CHAR);
    pango_layout_set_ellipsize(layout, PANGO_ELLIPSIZE_END);
    pango_layout_set_text(layout, text && *text ? text : "Click to write a note", -1);
    widget_color(canvas, WIDGET_TEXT, "f5e9ff", 1);
    cairo_move_to(canvas, 16, 47);
    pango_cairo_show_layout(canvas, layout);
    g_object_unref(layout);
    g_free(text);
}

static void edit_widget_notes(void)
{
    GtkWidget *dialog = gtk_dialog_new_with_buttons("Notes", NULL, GTK_DIALOG_MODAL,
        "Cancel", GTK_RESPONSE_CANCEL, "Save", GTK_RESPONSE_ACCEPT, NULL);
    setting_window_visual(dialog);
    gtk_window_set_default_size(GTK_WINDOW(dialog), 420, 270);
    gtk_window_set_position(GTK_WINDOW(dialog), GTK_WIN_POS_CENTER);
    GtkWidget *content = gtk_dialog_get_content_area(GTK_DIALOG(dialog));
    gtk_container_set_border_width(GTK_CONTAINER(content), 12);

    GtkWidget *scroll = gtk_scrolled_window_new(NULL, NULL);
    GtkWidget *view = gtk_text_view_new();
    gtk_text_view_set_wrap_mode(GTK_TEXT_VIEW(view), GTK_WRAP_WORD_CHAR);
    gtk_text_view_set_left_margin(GTK_TEXT_VIEW(view), 8);
    gtk_text_view_set_right_margin(GTK_TEXT_VIEW(view), 8);
    gtk_text_view_set_top_margin(GTK_TEXT_VIEW(view), 8);
    gtk_container_add(GTK_CONTAINER(scroll), view);
    gtk_box_pack_start(GTK_BOX(content), scroll, TRUE, TRUE, 0);
    GtkTextBuffer *buffer = gtk_text_view_get_buffer(GTK_TEXT_VIEW(view));
    char *existing = widget_notes_text();
    if (existing)
        gtk_text_buffer_set_text(buffer, existing, -1);
    g_free(existing);
    GtkWidget *status = gtk_label_new(NULL);
    gtk_label_set_xalign(GTK_LABEL(status), 0);
    gtk_label_set_line_wrap(GTK_LABEL(status), TRUE);
    gtk_box_pack_start(GTK_BOX(content), status, FALSE, FALSE, 8);

    gtk_widget_show_all(dialog);
    gtk_widget_grab_focus(view);
    while (gtk_dialog_run(GTK_DIALOG(dialog)) == GTK_RESPONSE_ACCEPT) {
        GtkTextIter start, end;
        gtk_text_buffer_get_bounds(buffer, &start, &end);
        char *text = gtk_text_buffer_get_text(buffer, &start, &end, FALSE);
        if (strlen(text) > 16384) {
            gtk_label_set_text(GTK_LABEL(status), "This note is too long. Shorten it before saving.");
            g_free(text);
            continue;
        }
        char *path = widget_notes_path();
        char *directory = g_path_get_dirname(path);
        g_mkdir_with_parents(directory, 0700);
        GError *error = NULL;
        gboolean saved = g_file_set_contents_full(path, text, -1,
            G_FILE_SET_CONTENTS_CONSISTENT, 0600, &error);
        g_free(directory);
        g_free(path);
        g_free(text);
        if (saved) {
            gtk_widget_queue_draw(cards[WIDGET_NOTES]);
            break;
        }
        gtk_label_set_text(GTK_LABEL(status), error->message);
        g_error_free(error);
    }
    gtk_widget_destroy(dialog);
}
