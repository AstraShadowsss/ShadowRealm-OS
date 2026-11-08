/* User-owned menu preferences. Application identities stay stable when labels change. */
static GKeyFile *menu_preferences;
static GtkCssProvider *menu_size_provider;
static void fill(void);
static void choose(GtkButton*,gpointer);
static gboolean favorite_app(App*);
static const char *menu_category_keys[]={"Favorites","All applications","Games","Browsers","Communication","Internet","Office","Media","Graphics","Files","Utilities","Security","System","Settings","Development","Other"};
static const char *menu_category_labels[]={"Favorites","All Apps","Games","Web Browsers","Communication","Internet","Office","Music & Video","Graphics","Files & Storage","Utilities","Security & Privacy","System & Updates","Settings","Development","Other"};
static char *menu_app_key(App *app){
 const char *id=app->info?g_app_info_get_id(app->info):NULL;
 return id?g_strdup(id):g_strconcat("builtin:",app->command?app->command:"",NULL);
}
static char *menu_preferences_path(void){return g_build_filename(g_get_user_config_dir(),"shadowrealm-os","menu.ini",NULL);}
static void menu_preferences_load(void){
 if(menu_preferences)g_key_file_unref(menu_preferences);
 menu_preferences=g_key_file_new();char *path=menu_preferences_path();g_key_file_load_from_file(menu_preferences,path,G_KEY_FILE_NONE,NULL);g_free(path);
 for(guint i=0;i<appdata->len;i++){App *app=g_ptr_array_index(appdata,i);char *key=menu_app_key(app);g_free(app->category_override);app->category_override=g_key_file_get_string(menu_preferences,"Categories",key,NULL);g_free(key);}
}
static gboolean menu_preferences_save(void){
 gsize length;char *data=g_key_file_to_data(menu_preferences,&length,NULL),*path=menu_preferences_path(),*directory=g_path_get_dirname(path);g_mkdir_with_parents(directory,0700);
 GFile *file=g_file_new_for_path(path);GError *error=NULL;
 gboolean ok=g_file_replace_contents(file,data,length,NULL,FALSE,G_FILE_CREATE_PRIVATE|G_FILE_CREATE_REPLACE_DESTINATION,NULL,NULL,&error);
 if(!ok){GtkWidget *message=gtk_message_dialog_new(menu_window?GTK_WINDOW(menu_window):NULL,GTK_DIALOG_MODAL,GTK_MESSAGE_ERROR,GTK_BUTTONS_CLOSE,"Could not save menu preferences: %s",error->message);gtk_dialog_run(GTK_DIALOG(message));gtk_widget_destroy(message);g_error_free(error);}
 g_object_unref(file);g_free(data);g_free(path);g_free(directory);return ok;
}
static gboolean menu_saved_favorite(App *app){
 gsize count=0;char **items=g_key_file_get_string_list(menu_preferences,"Favorites","Items",&count,NULL),*key=menu_app_key(app);gboolean found=FALSE;
 for(gsize i=0;i<count;i++)if(!strcmp(items[i],key)){found=TRUE;break;}
 g_strfreev(items);g_free(key);return found;
}
static void menu_favorites_initialize(void){
 if(g_key_file_has_key(menu_preferences,"Favorites","Items",NULL))return;
 GPtrArray *items=g_ptr_array_new_with_free_func(g_free);
 for(guint i=0;i<appdata->len;i++){App *app=g_ptr_array_index(appdata,i);if(favorite_app(app))g_ptr_array_add(items,menu_app_key(app));}
 g_key_file_set_string_list(menu_preferences,"Favorites","Items",(const gchar*const*)items->pdata,items->len);g_ptr_array_unref(items);
}
static void menu_toggle_favorite(GtkMenuItem *item,gpointer data){
 (void)item;App *app=data;menu_favorites_initialize();gboolean remove=menu_saved_favorite(app);char *key=menu_app_key(app);gsize count=0;char **old=g_key_file_get_string_list(menu_preferences,"Favorites","Items",&count,NULL);GPtrArray *items=g_ptr_array_new_with_free_func(g_free);
 for(gsize i=0;i<count;i++)if(strcmp(old[i],key))g_ptr_array_add(items,g_strdup(old[i]));
 if(!remove)g_ptr_array_add(items,g_strdup(key));
 g_key_file_set_string_list(menu_preferences,"Favorites","Items",(const gchar*const*)items->pdata,items->len);menu_preferences_save();g_ptr_array_unref(items);g_strfreev(old);g_free(key);
}
static void menu_assign_category(App *app,const char *target){
 char *key=menu_app_key(app);g_free(app->category_override);app->category_override=target&&*target?g_strdup(target):NULL;
 if(app->category_override)g_key_file_set_string(menu_preferences,"Categories",key,target);else g_key_file_remove_key(menu_preferences,"Categories",key,NULL);
 menu_preferences_save();g_free(key);
}
static void menu_move_category(GtkMenuItem *item,gpointer data){menu_assign_category(data,g_object_get_data(G_OBJECT(item),"category-key"));}
static void menu_create_category(GtkMenuItem *item,gpointer data){
 (void)item;GtkWidget *dialog=gtk_dialog_new_with_buttons("New Category",GTK_WINDOW(menu_window),GTK_DIALOG_MODAL,"Cancel",GTK_RESPONSE_CANCEL,"Create & Move",GTK_RESPONSE_OK,NULL);
 GtkWidget *entry=gtk_entry_new();gtk_entry_set_placeholder_text(GTK_ENTRY(entry),"Category name");gtk_entry_set_max_length(GTK_ENTRY(entry),40);gtk_container_set_border_width(GTK_CONTAINER(gtk_dialog_get_content_area(GTK_DIALOG(dialog))),18);gtk_container_add(GTK_CONTAINER(gtk_dialog_get_content_area(GTK_DIALOG(dialog))),entry);gtk_widget_show_all(dialog);
 if(gtk_dialog_run(GTK_DIALOG(dialog))==GTK_RESPONSE_OK){
  char *name=g_strdup(gtk_entry_get_text(GTK_ENTRY(entry)));g_strstrip(name);
  if(*name){gsize count=0;char **old=g_key_file_get_string_list(menu_preferences,"Menu","CustomCategories",&count,NULL);GPtrArray *items=g_ptr_array_new_with_free_func(g_free);gboolean exists=FALSE;
   for(gsize i=0;i<count;i++){g_ptr_array_add(items,g_strdup(old[i]));if(!g_ascii_strcasecmp(old[i],name))exists=TRUE;}
   if(!exists)g_ptr_array_add(items,g_strdup(name));g_key_file_set_string_list(menu_preferences,"Menu","CustomCategories",(const gchar*const*)items->pdata,items->len);
   char *key=g_strconcat("custom:",name,NULL);menu_assign_category(data,key);g_free(key);g_ptr_array_unref(items);g_strfreev(old);
  }g_free(name);
 }gtk_widget_destroy(dialog);
}
static GtkWidget *menu_category_submenu(App *app){
 GtkWidget *menu=gtk_menu_new();
 for(guint i=2;i<G_N_ELEMENTS(menu_category_keys);i++){GtkWidget *item=gtk_menu_item_new_with_label(menu_category_labels[i]);g_object_set_data_full(G_OBJECT(item),"category-key",g_strdup(menu_category_keys[i]),g_free);g_signal_connect(item,"activate",G_CALLBACK(menu_move_category),app);gtk_menu_shell_append(GTK_MENU_SHELL(menu),item);}
 gsize count=0;char **custom=g_key_file_get_string_list(menu_preferences,"Menu","CustomCategories",&count,NULL);
 for(gsize i=0;i<count;i++){GtkWidget *item=gtk_menu_item_new_with_label(custom[i]);g_object_set_data_full(G_OBJECT(item),"category-key",g_strconcat("custom:",custom[i],NULL),g_free);g_signal_connect(item,"activate",G_CALLBACK(menu_move_category),app);gtk_menu_shell_append(GTK_MENU_SHELL(menu),item);}g_strfreev(custom);
 GtkWidget *item=gtk_separator_menu_item_new();gtk_menu_shell_append(GTK_MENU_SHELL(menu),item);item=gtk_menu_item_new_with_label("Automatic Category");g_signal_connect(item,"activate",G_CALLBACK(menu_move_category),app);gtk_menu_shell_append(GTK_MENU_SHELL(menu),item);
 item=gtk_menu_item_new_with_label("New Category…");g_signal_connect(item,"activate",G_CALLBACK(menu_create_category),app);gtk_menu_shell_append(GTK_MENU_SHELL(menu),item);return menu;
}
static int menu_scale_percent(void){return g_key_file_has_key(menu_preferences,"Menu","Scale",NULL)?CLAMP(g_key_file_get_integer(menu_preferences,"Menu","Scale",NULL),80,140):100;}
static int menu_item_spacing(void){return g_key_file_has_key(menu_preferences,"Menu","Spacing",NULL)?CLAMP(g_key_file_get_integer(menu_preferences,"Menu","Spacing",NULL),0,10):3;}
static void menu_apply_size(void){
 if(!menu_size_provider){menu_size_provider=gtk_css_provider_new();gtk_style_context_add_provider_for_screen(gdk_screen_get_default(),GTK_STYLE_PROVIDER(menu_size_provider),GTK_STYLE_PROVIDER_PRIORITY_APPLICATION+2);}
 double points=10.0*menu_scale_percent()/100.0;int spacing=menu_item_spacing();char *css=g_strdup_printf(".shadow-launcher-menu label, .shadow-launcher-menu entry { font-size: %.1fpt; } .shadow-launcher-menu button { padding: %dpx 8px; } .shadow-launcher-menu button.menu-size-button { border: 1px solid currentColor; min-height: 28px; font-weight: bold; } .shadow-launcher-menu scrollbar.vertical slider { min-width: 8px; min-height: 25px; } .shadow-launcher-menu button.menu-close { font-weight: bold; border: 2px solid currentColor; min-height: 34px; }",points,spacing);
 GdkRGBA accent_color;
 GtkStyleContext *style=menu_window?gtk_widget_get_style_context(menu_window):NULL;
 if(!style || !gtk_style_context_lookup_color(style,"theme_selected_bg_color",&accent_color))
  gdk_rgba_parse(&accent_color,"#3478be");
 char hex[8];g_snprintf(hex,sizeof(hex),"#%02x%02x%02x",
   (unsigned)round(accent_color.red*255),(unsigned)round(accent_color.green*255),
   (unsigned)round(accent_color.blue*255));
 const double rgb[]={accent_color.red,accent_color.green,accent_color.blue};
 const double weights[]={.2126,.7152,.0722};
 double brightness=0;
 for(guint i=0;i<G_N_ELEMENTS(rgb);i++)
  brightness+=weights[i]*(rgb[i]<=.04045?rgb[i]/12.92:pow((rgb[i]+.055)/1.055,2.4));
 const char *selected_text=brightness>.18?"#111115":"#ffffff";
 char *skin=g_strdup_printf(
  "%s"
  "@define-color shadow_menu_accent %s;"
  ".shadow-launcher-menu button:not(.menu-size-button):not(.menu-close) { background-image:none; background-color:transparent; box-shadow:none; border:1px solid transparent; border-radius:4px; }"
  ".shadow-launcher-menu button:not(.menu-size-button):not(.menu-close):hover { background-color:alpha(@shadow_menu_accent,.16); border-color:alpha(@shadow_menu_accent,.48); }"
  ".shadow-launcher-menu button:not(.menu-size-button):not(.menu-close):checked { background-color:@shadow_menu_accent; color:%s; border-color:@shadow_menu_accent; }"
  ".shadow-launcher-menu button:focus { outline-color:@shadow_menu_accent; }"
  ".shadow-launcher-menu entry:focus, .shadow-launcher-menu searchentry:focus { border-color:@shadow_menu_accent; box-shadow:none; }",
  css,hex,selected_text);
 gtk_css_provider_load_from_data(menu_size_provider,skin,-1,NULL);g_free(skin);g_free(css);
 if(!menu_window)return;
 GdkDisplay *display=gdk_display_get_default();
 GdkMonitor *monitor=gdk_display_get_primary_monitor(display);
 if(!monitor)monitor=gdk_display_get_monitor(display,0);
 if(!monitor)return;
 GdkRectangle area;
 gdk_monitor_get_workarea(monitor,&area);
 int desired=650*menu_scale_percent()/100;
 GtkWidget *categories=g_object_get_data(G_OBJECT(menu_window),"category-scroll");
 if(categories)gtk_widget_set_size_request(categories,MIN(area.width/3,CLAMP(205*menu_scale_percent()/100,170,258)),-1);
 int width=MIN(area.width-16,desired), height=MIN(area.height-16,desired);
 gtk_window_move(GTK_WINDOW(menu_window),area.x+8,area.y+8);
 gtk_window_set_default_size(GTK_WINDOW(menu_window),MAX(1,width),MAX(1,height));
 gtk_window_resize(GTK_WINDOW(menu_window),MAX(1,width),MAX(1,height));
}
static void menu_size_changed(GtkRange *range,gpointer key){g_key_file_set_integer(menu_preferences,"Menu",key,(int)round(gtk_range_get_value(range)));menu_preferences_save();menu_apply_size();fill();}
static void menu_size_dialog(GtkButton *button,gpointer unused){
 (void)button;(void)unused;menu_interacting=TRUE;
 GtkWidget *dialog=gtk_dialog_new_with_buttons("Menu Size",GTK_WINDOW(menu_window),GTK_DIALOG_MODAL,"Done",GTK_RESPONSE_CLOSE,NULL);gtk_window_set_default_size(GTK_WINDOW(dialog),430,220);GtkWidget *box=gtk_dialog_get_content_area(GTK_DIALOG(dialog));gtk_container_set_border_width(GTK_CONTAINER(box),18);gtk_box_set_spacing(GTK_BOX(box),12);
 GtkWidget *label=gtk_label_new("Text and menu size (%)");gtk_box_pack_start(GTK_BOX(box),label,FALSE,FALSE,0);GtkWidget *scale=gtk_scale_new_with_range(GTK_ORIENTATION_HORIZONTAL,80,140,5);gtk_range_set_value(GTK_RANGE(scale),menu_scale_percent());g_signal_connect(scale,"value-changed",G_CALLBACK(menu_size_changed),"Scale");gtk_box_pack_start(GTK_BOX(box),scale,FALSE,FALSE,0);
 label=gtk_label_new("Space between items");gtk_box_pack_start(GTK_BOX(box),label,FALSE,FALSE,0);scale=gtk_scale_new_with_range(GTK_ORIENTATION_HORIZONTAL,0,10,1);gtk_range_set_value(GTK_RANGE(scale),menu_item_spacing());g_signal_connect(scale,"value-changed",G_CALLBACK(menu_size_changed),"Spacing");gtk_box_pack_start(GTK_BOX(box),scale,FALSE,FALSE,0);gtk_widget_show_all(dialog);gtk_dialog_run(GTK_DIALOG(dialog));gtk_widget_destroy(dialog);menu_interacting=FALSE;
}
