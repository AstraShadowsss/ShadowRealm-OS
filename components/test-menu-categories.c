/* Regression checks against the real menu classifier, including mixed tags. */
#define main shadow_desktop_main
#include "shadow-link-dock.c"
#undef main
#include <glib/gstdio.h>
int main(void) {
 struct { const char *id,*categories,*expected; } checks[]={
  {"librewolf.desktop","Network;WebBrowser;Security;","Browsers"},
  {"torbrowser.desktop","Network;WebBrowser;","Browsers"},
  {"torbrowser-settings.desktop","Network;WebBrowser;","Settings"},
  {"thunderbird.desktop","Network;Email;News;GTK;","Communication"},
  {"net.jami.Jami.desktop","Chat;Network;Telephony;","Communication"},
  {"gparted.desktop","System;Filesystem;","System"},
  {"xarchiver.desktop","Utility;Archiving;","Files"},
  {"xfburn.desktop","DiscBurning;Archiving;AudioVideo;","Media"},
  {"onboard.desktop","Utility;Accessibility;","Settings"},
  {"galculator.desktop","Utility;","Utilities"}
 };
 for(guint i=0;i<G_N_ELEMENTS(checks);i++) {
  GKeyFile *k=g_key_file_new();
  g_key_file_set_string(k,"Desktop Entry","Type","Application");
  g_key_file_set_string(k,"Desktop Entry","Name",checks[i].id);
  g_key_file_set_string(k,"Desktop Entry","Exec","/usr/bin/true");
  char *directory=g_dir_make_tmp("shadow-menu-test-XXXXXX",NULL);
  char *path=g_build_filename(directory,checks[i].id,NULL);
  char *data=g_key_file_to_data(k,NULL,NULL);g_file_set_contents(path,data,-1,NULL);g_free(data);
  GDesktopAppInfo *info=g_desktop_app_info_new_from_filename(path);
  if(!info||g_strcmp0(g_app_info_get_id(G_APP_INFO(info)),checks[i].id))return 3;
  App a={0};a.category=(char*)checks[i].categories;a.info=G_APP_INFO(info);
  if(g_strcmp0(application_group(&a),checks[i].expected))return 1;
  a.category_override="My Applications";
  if(g_strcmp0(application_group(&a),"My Applications"))return 2;
  g_object_unref(info);g_key_file_unref(k);g_unlink(path);g_rmdir(directory);g_free(path);g_free(directory);
 }
 puts("PASS mixed-category roles and manual overrides");return 0;
}
