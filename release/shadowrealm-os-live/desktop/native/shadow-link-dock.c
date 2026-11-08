#define _DEFAULT_SOURCE
#include <gtk/gtk.h>
#include <sys/prctl.h>
#include <gio/gdesktopappinfo.h>
#include <sys/statvfs.h>
#include <sys/stat.h>
#include <sys/utsname.h>
#include <ifaddrs.h>
#include <net/if.h>
#include <arpa/inet.h>
#include <dirent.h>
#include <unistd.h>
#include <signal.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static double cpu,ram,swp,diskpct,history[40];
static double ram_used_mib,ram_total_mib;
static int professional_mode;
static char plain_accent[7]="929ba5";
static char firewall_status[48]="NOT VERIFIED";
static char policy_status[48]="NOT VERIFIED";
static char tor_status[48]="TOR: CHECKING";
static double net_down_kib,net_up_kib;
static char active_if[IFNAMSIZ];
static void appearance_read(void){char *p=g_build_filename(g_get_home_dir(),".config","shadowrealm-os","appearance-mode",NULL);gchar*v=NULL;professional_mode=0;if(g_file_get_contents(p,&v,NULL,NULL)){professional_mode=g_str_has_prefix(v,"black-blue")?8:g_str_has_prefix(v,"blue-white")?9:(g_str_has_prefix(v,"white-silver-gold")||g_str_has_prefix(v,"professional-light"))?2:g_str_has_prefix(v,"professional")?1:g_str_has_prefix(v,"red-black")?3:g_str_has_prefix(v,"woodland")?4:g_str_has_prefix(v,"hacker")?5:g_str_has_prefix(v,"plain-dark")?6:g_str_has_prefix(v,"plain-light")?7:0;g_free(v);}g_free(p);p=g_build_filename(g_get_home_dir(),".config","shadowrealm-os","plain-accent",NULL);v=NULL;if(g_file_get_contents(p,&v,NULL,NULL)){g_strstrip(v);gboolean valid=strlen(v)==6;for(int i=0;valid&&i<6;i++)valid=g_ascii_isxdigit(v[i]);if(valid)memcpy(plain_accent,v,7);g_free(v);}g_free(p);}

static char iptext[64]="NO ADDRESS",iftext[32]="OFFLINE",vpn[40]="NO ACTIVE INTERFACE";
typedef struct { int pid; char name[64]; double cpu,mem; } ProcessRow;
enum { PROCESS_VISIBLE=6, PROCESS_MAX=256 };
static ProcessRow process_rows[PROCESS_MAX];
static int process_count, process_offset;
static unsigned long long lasttotal,lastidle;
static GtkWidget *cards[4],*cardwindows[4];
static void widgets_read(void);
static gboolean widget_enabled(int i);
static int widget_integer(const char*key,int fallback);
static void reflow_widgets(void);
static GdkPixbuf *brand;
static double scale=1;
static double widget_background_alpha=.98;
static const char *self;
static GtkWidget *heading(const char*title,const char*subtitle);
static void setting_window_visual(GtkWidget*w);
static void appearance_css_changed(GtkSettings *settings,GParamSpec *spec,gpointer provider){
 (void)settings;(void)spec;appearance_read();
 gchar *theme=NULL;g_object_get(gtk_settings_get_default(),"gtk-theme-name",&theme,NULL);char *p=g_build_filename(g_get_home_dir(),".themes",theme,"gtk-3.0","gtk.css",NULL);g_free(theme);
 if(g_file_test(p,G_FILE_TEST_IS_REGULAR))gtk_css_provider_load_from_path(GTK_CSS_PROVIDER(provider),p,NULL);else gtk_css_provider_load_from_data(GTK_CSS_PROVIDER(provider),"",-1,NULL);g_free(p);char*bp=g_build_filename(g_get_home_dir(),".local","share","shadow-link","logo.png",NULL);if(brand)g_object_unref(brand);brand=gdk_pixbuf_new_from_file_at_scale(bp,24,24,TRUE,NULL);g_free(bp);
}
static void color(cairo_t *c,const char *s,double a){
 if(professional_mode==8 || professional_mode==9){
  gboolean light=professional_mode==9;
  if(!strcmp(s,"04040b")||!strcmp(s,"080710"))s=light?"f6faff":"090e19";
  else if(!strcmp(s,"39243f"))s=light?"c2d6eb":"243b61";
  else if(strstr("fa12ed f04fff fc52f9 fc36ed f114dd",s))s=light?"4058aa":"7092ff";
  else if(strstr("00efff 04eaf5 00eafa 00f4ff 00f0ff 00eaff 19ebf5 00dce9",s))s=light?"1765ad":"52b4ff";
  else if(strstr("f5e9ff f4eaff f2e4fa f8f0ff f2e9f8 c7b4d6 baa3ce",s))s=light?"152d48":"edf5ff";
 }else if(professional_mode){
  if(!strcmp(s,"04040b")||!strcmp(s,"080710"))s=professional_mode==7?"f4f4f4":professional_mode==6?"202124":professional_mode==2?"f5f4ef":professional_mode==3?"100b0d":professional_mode==4?"19271c":professional_mode==5?"050a07":"111827";
  else if((professional_mode==2||professional_mode==7)&&!strcmp(s,"e5bb6a"))s="7b571c";
  else if(!strcmp(s,"39243f"))s=professional_mode==7?"d9dadd":professional_mode==6?"44474d":professional_mode==2?"d9e0e8":"293548";
  else if(strstr("fa12ed f04fff fc52f9 fc36ed f114dd",s))s=professional_mode>=6?plain_accent:professional_mode==2?"a78236":professional_mode==3?"e24b4b":professional_mode==4?"efbf49":professional_mode==5?"40f879":"7496bd";
  else if(strstr("00efff 04eaf5 00eafa 00f4ff 00f0ff 00eaff 19ebf5 00dce9 04eaf5",s))s=professional_mode>=6?plain_accent:professional_mode==2?"8e6b2c":professional_mode==3?"f5bbbb":professional_mode==4?"8bd445":professional_mode==5?"a5ffc0":"b0cee5";
  else if(strstr("f5e9ff f4eaff f2e4fa f8f0ff f2e9f8",s))s=professional_mode==7?"25272a":professional_mode==6?"e6e7e9":professional_mode==2?"172535":"edf2f7";
  else if(strstr("c7b4d6 baa3ce",s))s=professional_mode==7?"52565d":professional_mode==6?"c6c8cd":professional_mode==2?"42566c":"d0dae7";
 }
 unsigned r,g,b;sscanf(s,"%2x%2x%2x",&r,&g,&b);cairo_set_source_rgba(c,r/255.,g/255.,b/255.,a);}
static void txt(cairo_t*c,double x,double y,double size,const char*s,const char*co,int bold){color(c,co,1);cairo_select_font_face(c,"DejaVu Sans Mono",CAIRO_FONT_SLANT_NORMAL,bold?CAIRO_FONT_WEIGHT_BOLD:CAIRO_FONT_WEIGHT_NORMAL);cairo_set_font_size(c,size);cairo_move_to(c,x,y);cairo_show_text(c,s);}
static void txt_right(cairo_t*c,double right,double y,double size,const char*text,const char*co,int bold){cairo_text_extents_t ext;cairo_select_font_face(c,"DejaVu Sans Mono",CAIRO_FONT_SLANT_NORMAL,bold?CAIRO_FONT_WEIGHT_BOLD:CAIRO_FONT_WEIGHT_NORMAL);cairo_set_font_size(c,size);cairo_text_extents(c,text,&ext);txt(c,right-ext.x_advance,y,size,text,co,bold);}
static void line(cairo_t*c,double x,double y,double xx,double yy,const char*co,double w){color(c,co,1);cairo_set_line_width(c,w);cairo_move_to(c,x,y);cairo_line_to(c,xx,yy);cairo_stroke(c);}
static void frame(cairo_t*c,double w,double h,const char*title){
 color(c,"04040b",widget_background_alpha);cairo_move_to(c,12,1);cairo_line_to(c,w-12,1);cairo_line_to(c,w-1,12);cairo_line_to(c,w-1,h-12);cairo_line_to(c,w-12,h-1);cairo_line_to(c,12,h-1);cairo_line_to(c,1,h-12);cairo_line_to(c,1,12);cairo_close_path(c);cairo_fill_preserve(c);
 color(c,"fa12ed",.3);cairo_set_line_width(c,professional_mode?1:5);cairo_stroke_preserve(c);color(c,"f04fff",1);cairo_set_line_width(c,1.7);cairo_stroke(c);
 line(c,18,5,w-28,5,"fc52f9",1);line(c,20,h-5,w-20,h-5,"00efff",1.5);line(c,w-5,18,w-5,h-20,"00efff",1);
 if(brand){gdk_cairo_set_source_pixbuf(c,brand,10,10);cairo_paint(c);}txt(c,39,27,12,title,"fc36ed",1);line(c,12,37,w-12,37,"04eaf5",1);
 for(int i=0;i<39;i++){double v1=history[i],v2=history[i+1];line(c,w-63+i*.9,27-v1*.12,w-63+(i+1)*.9,27-v2*.12,i%2?"00eafa":"fc36ed",.9);}
}
static void bar(cairo_t*c,int y,const char*name,double value){char b[24];txt(c,14,y,12,name,"f5e9ff",0);color(c,"39243f",1);cairo_rectangle(c,68,y-11,124,12);cairo_fill(c);color(c,"f114dd",1);cairo_rectangle(c,69,y-10,fmin(122,1.22*value),10);cairo_fill(c);for(int i=0;i<122;i+=7)line(c,69+i,y-10,69+i,y,"080710",.8);snprintf(b,sizeof b,"%3.0f%%",value);txt(c,203,y,12,b,"00f4ff",1);}
static gboolean draw(GtkWidget*w,cairo_t*c,gpointer p){int k=GPOINTER_TO_INT(p);double ww=gtk_widget_get_allocated_width(w)/scale,hh=gtk_widget_get_allocated_height(w)/scale;cairo_set_operator(c,CAIRO_OPERATOR_SOURCE);cairo_set_source_rgba(c,0,0,0,0);cairo_paint(c);cairo_set_operator(c,CAIRO_OPERATOR_OVER);cairo_scale(c,scale,scale);
 const char *names[]={"SYSTEM OVERVIEW","NETWORK // LIVE","PROCESSES","SHADOW SHIELD"};char process_title[40];
 if(k==2&&process_count){
  g_snprintf(process_title,sizeof process_title,"PROCESSES  %d-%d/%d",
             process_offset+1,MIN(process_count,process_offset+PROCESS_VISIBLE),process_count);
 }
 frame(c,ww,hh,k==2&&process_count?process_title:names[k]);
 if(k==0){bar(c,61,"CPU",cpu);bar(c,85,"RAM",ram);bar(c,109,"SWAP",swp);bar(c,133,"DISK",diskpct);}
 if(k==1){char rates[80];txt(c,15,61,12,iftext,"f8f0ff",1);txt(c,15,81,12,iptext,"00f0ff",1);snprintf(rates,sizeof rates,"DOWN  %.1f KiB/s",net_down_kib);txt(c,15,105,11,rates,"f5e9ff",0);snprintf(rates,sizeof rates,"UP    %.1f KiB/s",net_up_kib);txt(c,15,128,11,rates,"f5e9ff",0);}
 if(k==2){double pid_right=55,name_x=66,cpu_right=ww-66,mem_right=ww-15;txt_right(c,pid_right,58,11,"PID","f4eaff",1);txt(c,name_x,58,11,"NAME","f4eaff",1);txt_right(c,cpu_right,58,11,"CPU%","f4eaff",1);txt_right(c,mem_right,58,11,"MEM%","f4eaff",1);for(int i=0;i<PROCESS_VISIBLE&&i+process_offset<process_count;i++){ProcessRow*r=&process_rows[i+process_offset];char pid[24],name[15],pc[24],pm[24];snprintf(pid,sizeof pid,"%d",r->pid);snprintf(name,sizeof name,"%.14s",r->name);snprintf(pc,sizeof pc,"%.1f",r->cpu);snprintf(pm,sizeof pm,"%.1f",r->mem);const char*co=i%2?"f2e4fa":"19ebf5";double y=80+i*18;txt_right(c,pid_right,y,10,pid,co,0);txt(c,name_x,y,10,name,co,0);txt_right(c,cpu_right,y,10,pc,co,0);txt_right(c,mem_right,y,10,pm,co,0);}}
 if(k==3){txt(c,15,61,11,"FIREWALL","f2e9f8",0);txt(c,15,79,11,firewall_status,"e5bb6a",1);txt(c,15,102,11,policy_status,"c7b4d6",0);char vp[64];snprintf(vp,sizeof vp,"VPN: %.28s",vpn);txt(c,15,124,10,vp,"00dce9",0);txt(c,15,146,10,tor_status,"c7b4d6",0);}
 return FALSE;}
static void refresh_stats(void){FILE*f=fopen("/proc/stat","r");unsigned long long u,n,s,id,iw,irq,si,st;if(f){if(fscanf(f,"cpu %llu %llu %llu %llu %llu %llu %llu %llu",&u,&n,&s,&id,&iw,&irq,&si,&st)==8){unsigned long long t=u+n+s+id+iw+irq+si+st,ii=id+iw;if(lasttotal&&t>lasttotal)cpu=100.*(1.-(double)(ii-lastidle)/(t-lasttotal));lasttotal=t;lastidle=ii;}fclose(f);}unsigned long mt=0,ma=0,ss=0,sf=0,v;char b[256],key[64];f=fopen("/proc/meminfo","r");if(f){while(fgets(b,sizeof b,f)){if(sscanf(b,"%63s %lu",key,&v)==2){if(!strcmp(key,"MemTotal:"))mt=v;if(!strcmp(key,"MemAvailable:"))ma=v;if(!strcmp(key,"SwapTotal:"))ss=v;if(!strcmp(key,"SwapFree:"))sf=v;}}fclose(f);}ram=mt?100.*(mt-ma)/mt:0;ram_used_mib=(mt-ma)/1024.;ram_total_mib=mt/1024.;swp=ss?100.*(ss-sf)/ss:0;struct statvfs fs;if(!statvfs("/",&fs)&&fs.f_blocks)diskpct=100.*(fs.f_blocks-fs.f_bfree)/fs.f_blocks;
 active_if[0]=0;strcpy(iptext,"NO ADDRESS");strcpy(iftext,"OFFLINE");strcpy(vpn,"NO ACTIVE INTERFACE");struct ifaddrs*a=NULL;if(!getifaddrs(&a)){for(struct ifaddrs*i=a;i;i=i->ifa_next){if(!i->ifa_addr||i->ifa_addr->sa_family!=AF_INET||!(i->ifa_flags&IFF_UP)||(i->ifa_flags&IFF_LOOPBACK))continue;if(!strncmp(i->ifa_name,"tun",3)||!strncmp(i->ifa_name,"wg",2)||!strncmp(i->ifa_name,"tap",3)){snprintf(vpn,sizeof vpn,"%s UP",i->ifa_name);continue;}snprintf(active_if,sizeof active_if,"%s",i->ifa_name);snprintf(iftext,sizeof iftext,"%s // UP",i->ifa_name);inet_ntop(AF_INET,&((struct sockaddr_in*)i->ifa_addr)->sin_addr,iptext,sizeof iptext);}freeifaddrs(a);}
 static unsigned long long old_rx,old_tx;static gint64 net_time;static char old_if[IFNAMSIZ];unsigned long long rx=0,tx=0;char netpath[256];gint64 stamp=g_get_monotonic_time();
 if(active_if[0]){snprintf(netpath,sizeof netpath,"/sys/class/net/%s/statistics/rx_bytes",active_if);FILE*nf=fopen(netpath,"r");if(nf){fscanf(nf,"%llu",&rx);fclose(nf);}snprintf(netpath,sizeof netpath,"/sys/class/net/%s/statistics/tx_bytes",active_if);nf=fopen(netpath,"r");if(nf){fscanf(nf,"%llu",&tx);fclose(nf);}}
 net_down_kib=net_up_kib=0;if(net_time&&stamp>net_time&&!strcmp(active_if,old_if)&&rx>=old_rx&&tx>=old_tx){double seconds=(stamp-net_time)/1000000.;net_down_kib=(rx-old_rx)/1024./seconds;net_up_kib=(tx-old_tx)/1024./seconds;}old_rx=rx;old_tx=tx;net_time=stamp;g_strlcpy(old_if,active_if,sizeof old_if);
 for(int i=0;i<39;i++){history[i]=history[i+1];}history[39]=cpu;
 f=popen("LC_ALL=C ps -eo pid=,pcpu=,pmem=,comm= --sort=-pcpu 2>/dev/null | head -256","r");
 process_count=0;
 while(f&&process_count<PROCESS_MAX&&fgets(b,sizeof b,f)){
  ProcessRow *row=&process_rows[process_count];
  if(sscanf(b,"%d %lf %lf %63[^\n]",&row->pid,&row->cpu,&row->mem,row->name)==4)
   process_count++;
 }
 if(f)pclose(f);
 process_offset=CLAMP(process_offset,0,MAX(0,process_count-PROCESS_VISIBLE));
}
static gboolean tick(gpointer unused){double previous_opacity=widget_background_alpha;char*opacity_path=g_build_filename(g_get_home_dir(),".config","shadowrealm-os","transparency.ini",NULL);GKeyFile*opacity=g_key_file_new();if(g_key_file_load_from_file(opacity,opacity_path,G_KEY_FILE_NONE,NULL)&&g_key_file_has_key(opacity,"Appearance","widget-opacity",NULL))widget_background_alpha=CLAMP(g_key_file_get_integer(opacity,"Appearance","widget-opacity",NULL),0,100)/100.;g_key_file_unref(opacity);g_free(opacity_path);if(fabs(previous_opacity-widget_background_alpha)>.001)for(int i=0;i<4;i++)if(cards[i])gtk_widget_queue_draw(cards[i]);appearance_read();static gint64 previous=0;widgets_read();reflow_widgets();gint64 now=g_get_monotonic_time();int interval=CLAMP(widget_integer("RefreshSeconds",2),1,15);if(now-previous>=interval*1000000LL){refresh_stats();previous=now;char tip[160];snprintf(tip,sizeof tip,"RAM: %.0f MiB used of %.0f MiB (%.1f%%). Updated every %d seconds.",ram_used_mib,ram_total_mib,ram,interval);if(cards[0])gtk_widget_set_tooltip_text(cards[0],tip);gchar*sec=NULL;if(g_file_get_contents("/run/shadowrealm-os/security-status",&sec,NULL,NULL)){g_strlcpy(firewall_status,strstr(sec,"firewall=active")?"ACTIVE / SSH TCP 22":"INACTIVE",sizeof firewall_status);g_strlcpy(policy_status,strstr(sec,"apparmor=enforcing")?"APPARMOR: ENFORCING":strstr(sec,"apparmor=enabled")?"APPARMOR: ENABLED":"APPARMOR: NOT ACTIVE",sizeof policy_status);g_strlcpy(tor_status,strstr(sec,"tor=running")?"TOR: SERVICE RUNNING":strstr(sec,"tor=stopped")?"TOR: STOPPED":"TOR: NOT INSTALLED",sizeof tor_status);char*vi=strstr(sec,"vpn_interface=");if(vi){vi+=14;char*end=strchr(vi,'\n');int length=end?end-vi:strlen(vi);if(length>0)snprintf(vpn,sizeof vpn,"%.*s CONNECTED",MIN(length,20),vi);}g_free(sec);}for(int i=0;i<4;i++)if(cards[i])gtk_widget_queue_draw(cards[i]);}return G_SOURCE_CONTINUE;}
static void reflow_widgets(void){GdkDisplay*d=gdk_display_get_default();GdkMonitor*m=gdk_display_get_primary_monitor(d);if(!m)m=gdk_display_get_monitor(d,0);GdkRectangle r;gdk_monitor_get_geometry(m,&r);int h[]={151,145,197,163},total=0;for(int i=0;i<4;i++)if(widget_enabled(i))total+=h[i]+12;scale=fmin(1.2,fmax(.68,(r.height-125)/685.))*CLAMP(widget_integer("ScalePercent",100),70,120)/100.;if(total)scale=fmin(scale,(r.height-125)/(double)total);int y=r.y+51,margin=CLAMP(widget_integer("RightMargin",12),0,150);for(int i=0;i<4;i++)if(cardwindows[i]){if(!widget_enabled(i)){gtk_widget_hide(cardwindows[i]);continue;}gtk_widget_set_size_request(cards[i],270*scale,h[i]*scale);gtk_window_resize(GTK_WINDOW(cardwindows[i]),270*scale,h[i]*scale);gtk_window_move(GTK_WINDOW(cardwindows[i]),r.x+r.width-270*scale-margin,y);gtk_widget_show(cardwindows[i]);y+=(h[i]+12)*scale;}}
static gboolean process_scroll(GtkWidget *widget,GdkEventScroll *event,gpointer unused){
 (void)unused;
 double dy=0;
 if(event->direction==GDK_SCROLL_DOWN)dy=1;
 else if(event->direction==GDK_SCROLL_UP)dy=-1;
 else if(event->direction==GDK_SCROLL_SMOOTH){
  double dx;gdk_event_get_scroll_deltas((GdkEvent*)event,&dx,&dy);
 }
 if(dy==0)return FALSE;
 process_offset=CLAMP(process_offset+(dy>0?3:-3),0,MAX(0,process_count-PROCESS_VISIBLE));
 (void)widget;gtk_widget_queue_draw(cards[2]);
 return TRUE;
}
static void widgets(void){widgets_read();GdkDisplay*d=gdk_display_get_default();GdkMonitor*m=gdk_display_get_primary_monitor(d);if(!m)m=gdk_display_get_monitor(d,0);GdkRectangle r;gdk_monitor_get_geometry(m,&r);scale=fmin(1.2,fmax(.68,(r.height-125)/685.));int h[]={151,145,197,163};int y=r.y+51;for(int i=0;i<4;i++){GtkWidget*w=gtk_window_new(GTK_WINDOW_TOPLEVEL);cardwindows[i]=w;gtk_window_set_title(GTK_WINDOW(w),"Shadow Link · Live Status");gtk_window_set_decorated(GTK_WINDOW(w),FALSE);gtk_window_set_resizable(GTK_WINDOW(w),FALSE);gtk_window_set_skip_taskbar_hint(GTK_WINDOW(w),TRUE);gtk_window_set_skip_pager_hint(GTK_WINDOW(w),TRUE);gtk_window_set_accept_focus(GTK_WINDOW(w),FALSE);gtk_window_set_type_hint(GTK_WINDOW(w),GDK_WINDOW_TYPE_HINT_NORMAL);gtk_window_set_keep_below(GTK_WINDOW(w),TRUE);gtk_window_stick(GTK_WINDOW(w));GdkVisual*v=gdk_screen_get_rgba_visual(gtk_widget_get_screen(w));if(v)gtk_widget_set_visual(w,v);gtk_widget_set_app_paintable(w,TRUE);cards[i]=gtk_drawing_area_new();
 if(i==2){
  gtk_widget_add_events(w,GDK_SCROLL_MASK|GDK_SMOOTH_SCROLL_MASK);
  g_signal_connect(w,"scroll-event",G_CALLBACK(process_scroll),NULL);
  gtk_widget_add_events(cards[i],GDK_SCROLL_MASK|GDK_SMOOTH_SCROLL_MASK);
  g_signal_connect(cards[i],"scroll-event",G_CALLBACK(process_scroll),NULL);
  gtk_widget_set_tooltip_text(cards[i],"Scroll to see more processes.");
 }
 gtk_widget_set_size_request(cards[i],270*scale,h[i]*scale);gtk_container_add(GTK_CONTAINER(w),cards[i]);g_signal_connect(cards[i],"draw",G_CALLBACK(draw),GINT_TO_POINTER(i));gtk_window_move(GTK_WINDOW(w),r.x+r.width-270*scale-12,y);y+=(h[i]+12)*scale;gtk_widget_show_all(w);}tick(NULL);g_timeout_add_seconds(1,tick,NULL);}
typedef struct {char *name,*command,*category;GAppInfo*info;char*category_override;} App;
static int menu_scale_percent(void);
static GPtrArray*appdata;static GtkWidget*list,*searchbox;
static const char *category="Favorites";
/* The XFCE panel launches a new process on every press. GtkApplication's
   session-bus application ID forwards presses to one existing process. */
static GtkWidget *menu_window=NULL;
static guint menu_hide_timer=0;
static gboolean menu_interacting=FALSE;
static void menu_close(GtkWidget*unused,gpointer p){
 (void)unused;(void)p;
 if(menu_window)gtk_widget_destroy(menu_window);
}
static void menu_destroyed(GtkWidget*w,gpointer p){
 (void)w;(void)p;
 if(menu_hide_timer){g_source_remove(menu_hide_timer);menu_hide_timer=0;}
 menu_window=NULL;
}
static gboolean menu_finish_dismiss(gpointer p){
 (void)p;
 menu_hide_timer=0;
 if(menu_window)gtk_widget_destroy(menu_window);
 return G_SOURCE_REMOVE;
}
static gboolean menu_focus_out(GtkWidget*w,GdkEventFocus*e,gpointer p){
 (void)e;(void)p;
 if(menu_interacting || w!=menu_window || !gtk_widget_get_visible(w))return FALSE;
 /* Hide immediately on outside click. Keep the process registered briefly
    so the same click on the panel Menu button can toggle, not reopen. */
 gtk_widget_hide(w);
 if(menu_hide_timer)g_source_remove(menu_hide_timer);
 menu_hide_timer=g_timeout_add(800,menu_finish_dismiss,NULL);
 return FALSE;
}
static gboolean menu_focus_in(GtkWidget*w,GdkEventFocus*e,gpointer p){
 (void)w;(void)e;(void)p;
 if(menu_hide_timer){g_source_remove(menu_hide_timer);menu_hide_timer=0;}
 return FALSE;
}

static void launch(GtkButton*b,gpointer p){if(menu_interacting)return;App*a=p;GError*err=NULL;if(a->info)g_app_info_launch(a->info,NULL,NULL,&err);else g_spawn_command_line_async(a->command,&err);if(err){GtkWidget*m=gtk_message_dialog_new(NULL,0,GTK_MESSAGE_ERROR,GTK_BUTTONS_CLOSE,"%s",err->message);gtk_dialog_run(GTK_DIALOG(m));gtk_widget_destroy(m);g_error_free(err);}else menu_close(NULL,NULL);}
/* Icon mapping for the built-in Shadow Link shortcuts. System .desktop
 * applications use their own GIcon rather than category guesses. */
static GtkWidget*shadow_menu_icon(App*a){
 int pixels=24*menu_scale_percent()/100;
 if(a->info){
  GIcon *gicon=g_app_info_get_icon(a->info);
  if(gicon){
   GtkWidget *img=gtk_image_new_from_gicon(gicon,GTK_ICON_SIZE_MENU);
   gtk_image_set_pixel_size(GTK_IMAGE(img),pixels);
   return img;
  }
 }
 if(!g_strcmp0(a->name,"Display settings"))
  return gtk_image_new_from_icon_name("org.xfce.settings.display",GTK_ICON_SIZE_MENU);
 static const struct {const char*name;const char*icon;} mapping[]={
  {"Terminal","terminal"},{"Shadow Calendar","calendar"},{"Shadow Calculator","calculator"},
  {"Shadow Clock","clock"},{"Shadow Widgets","widgets"},{"Shadow Network","network"},
  {"Shadow Audio","audio"},{"Shadow Bluetooth","bluetooth"},
  {"Shadow Media","media"},
  {"Thunderbird","email"},{"HexChat","irc"},{"Files","files"},
  {"Shadow Control Center","control-center"},{"Shadow Shield","shield"},
  {"Text Editor","editor"},{"Screenshot","screenshot"},{"Trash","trash"},
  {"Display settings","display"},{"Appearance","theme"},
  {"Software & Updates","software"},{"Choose Default Browser","browser"},
  {"Task manager","task-manager"},{"Web browser","browser"},
  {"Shadow Link","ORIGINAL-LOGO"},
 };
 const char *kind=NULL;
 for(guint i=0;i<G_N_ELEMENTS(mapping);i++){
  if(!g_strcmp0(a->name,mapping[i].name)){kind=mapping[i].icon;break;}
 }
 if(!kind){
  kind=(strstr(a->category,"Network")?"network":
        strstr(a->category,"Settings")?"settings":
        strstr(a->category,"Graphics")?"image-viewer":
        strstr(a->category,"AudioVideo")?"media":"app-menu");
 }
 char *path=g_strdup_printf("%s/.local/share/shadow-link/icons/%s.png",
                            g_get_home_dir(),
                            !g_strcmp0(kind,"ORIGINAL-LOGO")?"shadow-menu":
                            (const char*)kind);
 /* Build the correct filename: custom icon names use the shadow- prefix. */
 if(g_strcmp0(kind,"ORIGINAL-LOGO")!=0){
  g_free(path);
  path=g_strdup_printf("%s/.local/share/shadow-link/icons/shadow-%s.png",
                       g_get_home_dir(),kind);
 }
 GdkPixbuf *pix=gdk_pixbuf_new_from_file_at_scale(path,pixels,pixels,TRUE,NULL);
 g_free(path);
 if(pix){GtkWidget*img=gtk_image_new_from_pixbuf(pix);g_object_unref(pix);return img;}
 return gtk_image_new_from_icon_name("application-x-executable",GTK_ICON_SIZE_MENU);
}

static char*launcher_file(App*a){
 char*dir=g_build_filename(g_get_user_cache_dir(),"shadowrealm-os","launchers",NULL);g_mkdir_with_parents(dir,0700);
 char*slug=g_strdup(a->name);for(char*p=slug;*p;p++)if(!g_ascii_isalnum(*p)&&*p!='-'&&*p!='_')*p='_';
 char*name=g_strconcat(slug,".desktop",NULL);char*path=g_build_filename(dir,name,NULL);g_free(dir);g_free(name);g_free(slug);
 char*local_original=NULL;
 const char*original=a->info&&G_IS_DESKTOP_APP_INFO(a->info)?g_desktop_app_info_get_filename(G_DESKTOP_APP_INFO(a->info)):NULL;
 if(!original){char*apps=g_build_filename(g_get_user_data_dir(),"applications",NULL);GDir*d=g_dir_open(apps,0,NULL);const char*n;
 if(d){while((n=g_dir_read_name(d))){if(!g_str_has_suffix(n,".desktop"))continue;char*f=g_build_filename(apps,n,NULL);GDesktopAppInfo*info=g_desktop_app_info_new_from_filename(f);if(info&&g_ascii_strcasecmp(g_app_info_get_display_name(G_APP_INFO(info)),a->name)==0){local_original=g_strdup(f);g_object_unref(info);g_free(f);break;}if(info)g_object_unref(info);g_free(f);}g_dir_close(d);}g_free(apps);original=local_original;}

 if(original){gchar*data=NULL;gsize len;if(!g_file_get_contents(original,&data,&len,NULL)){g_free(path);return NULL;}g_file_set_contents(path,data,len,NULL);g_free(data);}
 else{GKeyFile*k=g_key_file_new();g_key_file_set_string(k,"Desktop Entry","Type","Application");g_key_file_set_string(k,"Desktop Entry","Name",a->name);g_key_file_set_string(k,"Desktop Entry","Exec",a->command);g_key_file_set_boolean(k,"Desktop Entry","Terminal",FALSE);
 const char*icon="application-x-executable";const char*cmd=a->command?a->command:"";
 if(strstr(cmd,"terminal"))icon="shadow-terminal";else if(strstr(cmd,"browser"))icon="shadow-browser";else if(strstr(cmd,"files"))icon="shadow-files";else if(strstr(cmd,"notes"))icon="shadow-editor";else if(strstr(cmd,"thunderbird"))icon="shadow-email";else if(strstr(cmd,"screenshot"))icon="shadow-screenshot";
 char*asset=g_str_has_prefix(icon,"shadow-")?g_strdup_printf("%s/.local/share/shadow-link/icons/%s.png",g_get_home_dir(),icon):NULL;g_key_file_set_string(k,"Desktop Entry","Icon",asset&&g_file_test(asset,G_FILE_TEST_IS_REGULAR)?asset:icon);g_free(asset);gsize len;gchar*data=g_key_file_to_data(k,&len,NULL);g_file_set_contents(path,data,len,NULL);g_free(data);g_key_file_unref(k);}
 g_free(local_original);chmod(path,0755);GFile*trusted=g_file_new_for_path(path);g_file_set_attribute_string(trusted,"metadata::trusted","true",G_FILE_QUERY_INFO_NONE,NULL,NULL);g_object_unref(trusted);return path;
}
static void pin_app(GtkMenuItem*i,gpointer data){App*a=data;char*src=launcher_file(a);if(!src)return;const char*desktop=g_get_user_special_dir(G_USER_DIRECTORY_DESKTOP);if(!desktop)desktop=g_get_home_dir();char*name=g_path_get_basename(src);char*dst=g_build_filename(desktop,name,NULL);GFile*f=g_file_new_for_path(src),*to=g_file_new_for_path(dst);GError*error=NULL;
 if(g_file_copy(f,to,G_FILE_COPY_NONE,NULL,NULL,NULL,&error)){chmod(dst,0755);g_file_set_attribute_string(to,"metadata::trusted","true",G_FILE_QUERY_INFO_NONE,NULL,NULL);}else if(error){GtkWidget*d=gtk_message_dialog_new(NULL,0,GTK_MESSAGE_ERROR,GTK_BUTTONS_CLOSE,"%s",error->message);gtk_dialog_run(GTK_DIALOG(d));gtk_widget_destroy(d);g_error_free(error);}
 g_object_unref(f);g_object_unref(to);g_free(name);g_free(src);g_free(dst);
}
static void app_context_done(GtkWidget*w,gpointer data){menu_interacting=FALSE;gtk_widget_destroy(w);menu_close(NULL,NULL);}
static void app_drag_begin(GtkWidget*w,GdkDragContext*c,gpointer data){menu_interacting=TRUE;}
static void app_drag_end(GtkWidget*w,GdkDragContext*c,gpointer data){menu_interacting=FALSE;menu_close(NULL,NULL);}
#include "menu-sizing-orbital.c"

static void dock_result(GObject *connection,GAsyncResult *result,gpointer unused){
 gchar *uri=unused;GError *error=NULL;
 GVariant *reply=g_dbus_connection_call_finish(G_DBUS_CONNECTION(connection),result,&error);
 if(reply){g_variant_unref(reply);g_free(uri);return;}
 gchar *remote=g_dbus_error_get_remote_error(error);
 gboolean fallback=uri&&g_strcmp0(remote,"org.freedesktop.DBus.Error.UnknownMethod")==0;
 g_free(remote);
 if(fallback){
  const gchar *arguments[]={uri,NULL};
  g_dbus_connection_call(G_DBUS_CONNECTION(connection),"org.xfce.Panel","/org/xfce/Panel","org.xfce.Panel",
      "AddNewItem",g_variant_new("(s^as)","launcher",arguments),NULL,G_DBUS_CALL_FLAGS_NONE,
      G_MAXINT,NULL,dock_result,NULL);
  g_error_free(error);g_free(uri);return;
 }
 g_free(uri);
 GtkWidget *dialog=gtk_message_dialog_new(NULL,0,GTK_MESSAGE_ERROR,GTK_BUTTONS_CLOSE,
    "Could not open the dock pinning dialog: %s",error->message);
 gtk_dialog_run(GTK_DIALOG(dialog));gtk_widget_destroy(dialog);g_error_free(error);
}
static gboolean dock_has_launcher(const char *command){
 if(!command)return FALSE;
 const gchar *argv[]={"xfconf-query","-c","xfce4-panel","-p","/panels/panel-2/plugin-ids",NULL};
 gchar *output=NULL;
 if(!g_spawn_sync(NULL,(gchar **)argv,NULL,G_SPAWN_SEARCH_PATH,NULL,NULL,&output,NULL,NULL,NULL))
  return FALSE;
 gchar **ids=g_strsplit(output?output:"","\n",-1);g_free(output);gboolean found=FALSE;
 for(guint i=0;ids[i]&&!found;i++){
  const char *id=ids[i];
  if(!*id||strspn(id,"0123456789")!=strlen(id))continue;
  gchar *dir=g_strdup_printf("%s/xfce4/panel/launcher-%s",g_get_user_config_dir(),id);
  GDir *entries=g_dir_open(dir,0,NULL);
  if(entries){const char *name;
   while((name=g_dir_read_name(entries))&&!found){
    if(!g_str_has_suffix(name,".desktop"))continue;
    gchar *path=g_build_filename(dir,name,NULL);
    GKeyFile *key=g_key_file_new();
    if(g_key_file_load_from_file(key,path,G_KEY_FILE_NONE,NULL)){
     gchar *exec=g_key_file_get_string(key,"Desktop Entry","Exec",NULL);
     found=g_strcmp0(exec,command)==0;g_free(exec);
    }
    g_key_file_unref(key);g_free(path);
   }
   g_dir_close(entries);
  }
  g_free(dir);
 }
 g_strfreev(ids);return found;
}
static void pin_dock(GtkMenuItem *item,gpointer data){
 (void)item;App *app=data;gchar *desktop=launcher_file(app);
 if(!desktop)return;
 GKeyFile *key=g_key_file_new();
 if(g_key_file_load_from_file(key,desktop,G_KEY_FILE_KEEP_TRANSLATIONS,NULL)){
  gchar *exec=g_key_file_get_string(key,"Desktop Entry","Exec",NULL);
  if(dock_has_launcher(exec)){
   GtkWidget *dialog=gtk_message_dialog_new(NULL,0,GTK_MESSAGE_INFO,GTK_BUTTONS_CLOSE,
      "%s is already pinned to the dock.",app->name);
   gtk_dialog_run(GTK_DIALOG(dialog));gtk_widget_destroy(dialog);
   g_free(exec);g_key_file_unref(key);g_free(desktop);return;
  }
  g_free(exec);
  gchar *icon=g_key_file_get_string(key,"Desktop Entry","Icon",NULL);
  if(icon&&g_str_has_prefix(icon,"shadowrealm-os-app-")){
   gchar *dock_icon=g_strconcat("shadowrealm-os-dock-",icon+strlen("shadowrealm-os-app-"),NULL);
   if(gtk_icon_theme_has_icon(gtk_icon_theme_get_default(),dock_icon))
    g_key_file_set_string(key,"Desktop Entry","Icon",dock_icon);
   g_free(dock_icon);
   g_key_file_save_to_file(key,desktop,NULL);
  }
  g_free(icon);
 }
 g_key_file_unref(key);
 gchar *uri=g_filename_to_uri(desktop,NULL,NULL);g_free(desktop);if(!uri)return;
 GDBusConnection *bus=g_bus_get_sync(G_BUS_TYPE_SESSION,NULL,NULL);
 if(bus){
  g_dbus_connection_call(bus,"org.xfce.Panel","/org/xfce/Panel","org.xfce.Panel",
      "AddLauncherToPanel",g_variant_new("(us)",2,uri),NULL,G_DBUS_CALL_FLAGS_NONE,
      10000,NULL,dock_result,g_strdup(uri));
  g_object_unref(bus);
 }
 g_free(uri);
}
static gboolean app_context(GtkWidget*w,GdkEventButton*event,gpointer data){if(event->button!=3)return FALSE;menu_interacting=TRUE;GtkWidget*m=gtk_menu_new(),*item=gtk_menu_item_new_with_label(favorite_app(data)?"Remove from Favorites":"Add to Favorites");gtk_menu_shell_append(GTK_MENU_SHELL(m),item);g_signal_connect(item,"activate",G_CALLBACK(menu_toggle_favorite),data);item=gtk_menu_item_new_with_label("Move to Category");gtk_menu_item_set_submenu(GTK_MENU_ITEM(item),menu_category_submenu(data));gtk_menu_shell_append(GTK_MENU_SHELL(m),item);gtk_menu_shell_append(GTK_MENU_SHELL(m),gtk_separator_menu_item_new());item=gtk_menu_item_new_with_label("Add to Desktop");gtk_menu_shell_append(GTK_MENU_SHELL(m),item);g_signal_connect(item,"activate",G_CALLBACK(pin_app),data);item=gtk_menu_item_new_with_label("Pin to Dock");gtk_menu_shell_append(GTK_MENU_SHELL(m),item);g_signal_connect(item,"activate",G_CALLBACK(pin_dock),data);g_signal_connect(m,"selection-done",G_CALLBACK(app_context_done),NULL);gtk_widget_show_all(m);gtk_menu_popup_at_pointer(GTK_MENU(m),(GdkEvent*)event);return TRUE;}

static void app_drag_data(GtkWidget*w,GdkDragContext*c,GtkSelectionData*selection,guint info,guint time,gpointer data){char*path=launcher_file(data);if(!path)return;char*uri=g_filename_to_uri(path,NULL,NULL);char*uris[]={uri,NULL};gtk_selection_data_set_uris(selection,uris);g_free(uri);g_free(path);}

static gboolean category_has(const char *categories,const char *token){
 char *wrapped=g_strdup_printf(";%s;",categories?categories:"");char *needle=g_strdup_printf(";%s;",token);gboolean found=strstr(wrapped,needle)!=NULL;g_free(wrapped);g_free(needle);return found;
}
static const char *application_group(App *a){
 if(a->category_override&&*a->category_override)return a->category_override;
 const char *c=a->category;
 if(category_has(c,"Security"))return "Security";
 if(category_has(c,"FileManager")||category_has(c,"Archiving")||category_has(c,"Filesystem")||category_has(c,"FileTools"))return "Files";
 if(category_has(c,"PackageManager"))return "System";
 if(category_has(c,"WebBrowser"))return "Browsers";
 if(category_has(c,"Email")||category_has(c,"IRCClient")||category_has(c,"Chat")||category_has(c,"InstantMessaging")||category_has(c,"Telephony")||category_has(c,"VideoConference"))return "Communication";
 if(category_has(c,"Settings")||category_has(c,"Accessibility")||category_has(c,"DesktopSettings")||category_has(c,"HardwareSettings")||category_has(c,"X-XFCE-SettingsDialog"))return "Settings";
 if(category_has(c,"Network"))return "Internet";
 if(category_has(c,"Office"))return "Office";
 if(category_has(c,"AudioVideo")||category_has(c,"Audio")||category_has(c,"Video"))return "Media";
 if(category_has(c,"Graphics"))return "Graphics";
 if(category_has(c,"Development"))return "Development";
 if(category_has(c,"Game"))return "Games";
 if(category_has(c,"System"))return "System";
 if(category_has(c,"Utility"))return "Utilities";
 return "Other";
}
static gboolean favorite_app(App *a){
 if(menu_preferences&&g_key_file_has_key(menu_preferences,"Favorites","Items",NULL))return menu_saved_favorite(a);
 if(a->info&&category_has(a->category,"FileManager"))return TRUE;
 if(a->info){GAppInfo *browser=g_app_info_get_default_for_type("x-scheme-handler/https",FALSE);gboolean same=browser&&g_app_info_equal(a->info,browser);if(browser)g_object_unref(browser);if(same)return TRUE;}
 const char *names[]={"Terminal","Thunar File Manager","Thunderbird","Shadow Control Center","Shadow Shield","Software & Updates"};
 for(guint i=0;i<G_N_ELEMENTS(names);i++)if(!g_ascii_strcasecmp(a->name,names[i]))return TRUE;
 return FALSE;
}
static gint alphabetical_apps(gconstpointer left,gconstpointer right){const App *a=*(App*const*)left,*b=*(App*const*)right;char *al=g_utf8_casefold(a->name,-1),*bl=g_utf8_casefold(b->name,-1);gint result=g_utf8_collate(al,bl);g_free(al);g_free(bl);return result;}
static void fill(void){GList*children=gtk_container_get_children(GTK_CONTAINER(list));for(GList*i=children;i;i=i->next)gtk_widget_destroy(i->data);g_list_free(children);char *q=g_utf8_strdown(gtk_entry_get_text(GTK_ENTRY(searchbox)),-1);for(guint i=0;i<appdata->len;i++){App*a=g_ptr_array_index(appdata,i);char*n=g_utf8_strdown(a->name,-1);gboolean match=strstr(n,q)!=NULL;g_free(n);if(!match){char *metadata=g_utf8_strdown(a->category,-1);match=strstr(metadata,q)!=NULL;g_free(metadata);}if(!match&&a->info){const char*d=g_app_info_get_description(a->info);char*description=g_utf8_strdown(d?d:"",-1);match=strstr(description,q)!=NULL;g_free(description);}if(!match)continue;if(!*q&&strcmp(category,"All applications")&&strcmp(category,"Favorites")&&strcmp(application_group(a),category))continue;if(!*q&&!strcmp(category,"Favorites")&&!favorite_app(a))continue;GtkWidget*b=gtk_button_new();GtkWidget*row=gtk_box_new(GTK_ORIENTATION_HORIZONTAL,10);GtkWidget*appicon=shadow_menu_icon(a);if(appicon)gtk_box_pack_start(GTK_BOX(row),appicon,FALSE,FALSE,0);GtkWidget*label=gtk_label_new(a->name);gtk_label_set_xalign(GTK_LABEL(label),0);gtk_label_set_ellipsize(GTK_LABEL(label),PANGO_ELLIPSIZE_END);gtk_label_set_max_width_chars(GTK_LABEL(label),34);gtk_box_pack_start(GTK_BOX(row),label,TRUE,TRUE,0);gtk_container_add(GTK_CONTAINER(b),row);gtk_widget_set_halign(b,GTK_ALIGN_FILL);gtk_style_context_add_class(gtk_widget_get_style_context(b),"app-item");g_signal_connect(b,"clicked",G_CALLBACK(launch),a);g_signal_connect(b,"button-press-event",G_CALLBACK(app_context),a);GtkTargetEntry target={"text/uri-list",0,0};gtk_drag_source_set(b,GDK_BUTTON1_MASK,&target,1,GDK_ACTION_COPY);g_signal_connect(b,"drag-data-get",G_CALLBACK(app_drag_data),a);g_signal_connect(b,"drag-begin",G_CALLBACK(app_drag_begin),a);g_signal_connect(b,"drag-end",G_CALLBACK(app_drag_end),a);gtk_widget_set_tooltip_text(b,"Click to open. Right-click to edit Favorites, move category, or add to Desktop.");gtk_box_pack_start(GTK_BOX(list),b,FALSE,FALSE,2);}g_free(q);gtk_widget_show_all(list);}
static void choose(GtkButton*b,gpointer p){if(GTK_IS_TOGGLE_BUTTON(b)&&!gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(b)))return;category=p;fill();}
static void changed(GtkEditable*e,gpointer p){fill();}
static void addcmd(const char*n,const char*c,const char*cat){char**args=NULL;int ac=0;g_shell_parse_argv(c,&ac,&args,NULL);char*found=ac?g_find_program_in_path(args[0]):NULL;g_strfreev(args);if(!found)return;g_free(found);App*a=g_new0(App,1);a->name=g_strdup(n);a->command=g_strdup(c);a->category=g_strdup(cat);g_ptr_array_add(appdata,a);}
static gboolean escape(GtkWidget*w,GdkEventKey*e,gpointer p){if(e->keyval==GDK_KEY_Escape){menu_close(NULL,NULL);return TRUE;}return FALSE;}
static void menu(void){appdata=g_ptr_array_new();addcmd("Terminal","shadow-terminal","System");addcmd("Shadow Calendar","shadow-link --calendar","Utility");addcmd("Shadow Calculator","shadow-link --calculator","Utility");addcmd("Shadow Clock","shadow-link --clock","Utility");addcmd("Shadow Widgets","shadow-link --widget-settings","Settings");addcmd("Shadow Network","shadow-link --network","Settings");addcmd("Shadow Audio","shadow-link --audio","Settings");addcmd("Shadow Bluetooth","shadow-link --bluetooth","Settings");addcmd("Shadow Control Center","shadow-link --control-center","Settings");addcmd("Shadow Shield","shadow-link --shield","Security");addcmd("Appearance","shadow-appearance","Settings");addcmd("Software & Updates","shadow-software","System");addcmd("Choose Default Browser","shadow-browser --settings","Settings");GList*all=g_app_info_get_all();for(GList*i=all;i;i=i->next){GAppInfo*info=i->data;if(!g_app_info_should_show(info))continue;
 const char*id=g_app_info_get_id(info);
 if(id && ((g_str_has_prefix(id,"shadow-") && !(G_IS_DESKTOP_APP_INFO(info) && category_has(g_desktop_app_info_get_categories(G_DESKTOP_APP_INFO(info)),"Game"))) ||
    !g_strcmp0(id,"xfce4-terminal-emulator.desktop") ||
    !g_strcmp0(id,"xfce4-terminal.desktop") ||
    !g_strcmp0(id,"xfce4-file-manager.desktop") ||
    !g_strcmp0(id,"xfce4-web-browser.desktop") ||
    !g_strcmp0(id,"xfce4-mail-reader.desktop")))continue;
 const char*display=g_app_info_get_display_name(info);
 gboolean duplicate=FALSE;
 for(guint j=0;j<appdata->len;j++){
   App*existing=g_ptr_array_index(appdata,j);
   if(g_ascii_strcasecmp(existing->name,display?display:"")==0){duplicate=TRUE;break;}
 }
 if(duplicate)continue;
 App*a=g_new0(App,1);a->name=g_strdup(g_app_info_get_display_name(info));a->info=g_object_ref(info);const char*cat=G_IS_DESKTOP_APP_INFO(info)?g_desktop_app_info_get_categories(G_DESKTOP_APP_INFO(info)):NULL;a->category=g_strdup(cat?cat:"");g_ptr_array_add(appdata,a);}g_list_free_full(all,g_object_unref);menu_preferences_load();g_ptr_array_sort(appdata,alphabetical_apps);
 GtkWidget*w=gtk_window_new(GTK_WINDOW_TOPLEVEL);setting_window_visual(w);menu_window=w;gtk_window_set_title(GTK_WINDOW(w),"Shadow Link");gtk_window_set_decorated(GTK_WINDOW(w),FALSE);gtk_window_set_default_size(GTK_WINDOW(w),650,650);gtk_window_set_keep_above(GTK_WINDOW(w),TRUE);gtk_window_set_skip_taskbar_hint(GTK_WINDOW(w),TRUE);gtk_style_context_add_class(gtk_widget_get_style_context(w),"shadow-menu");gtk_style_context_add_class(gtk_widget_get_style_context(w),"shadow-launcher-menu");GtkWidget*outer=gtk_box_new(GTK_ORIENTATION_VERTICAL,10);gtk_container_set_border_width(GTK_CONTAINER(outer),14);gtk_container_add(GTK_CONTAINER(w),outer);GtkWidget*title=heading(professional_mode==1?"Applications":"ShadowRealm-OS",professional_mode==1?"":"// SHADOW LINK");gtk_box_pack_start(GTK_BOX(outer),title,FALSE,FALSE,5);searchbox=gtk_search_entry_new();gtk_entry_set_placeholder_text(GTK_ENTRY(searchbox),"Search applications");gtk_box_pack_start(GTK_BOX(outer),searchbox,FALSE,FALSE,0);GtkWidget*body=gtk_box_new(GTK_ORIENTATION_HORIZONTAL,10);gtk_box_pack_start(GTK_BOX(outer),body,TRUE,TRUE,0);GtkWidget*categories=gtk_box_new(GTK_ORIENTATION_VERTICAL,2);GtkWidget*category_scroll=gtk_scrolled_window_new(NULL,NULL);gtk_scrolled_window_set_policy(GTK_SCROLLED_WINDOW(category_scroll),GTK_POLICY_NEVER,GTK_POLICY_AUTOMATIC);gtk_scrolled_window_set_overlay_scrolling(GTK_SCROLLED_WINDOW(category_scroll),FALSE);gtk_scrolled_window_set_min_content_height(GTK_SCROLLED_WINDOW(category_scroll),70);g_object_set_data(G_OBJECT(w),"category-scroll",category_scroll);gtk_container_add(GTK_CONTAINER(category_scroll),categories);gtk_box_pack_start(GTK_BOX(body),category_scroll,FALSE,FALSE,0);const char **cats=menu_category_keys,**labels=menu_category_labels;GSList*group=NULL;for(guint i=0;i<G_N_ELEMENTS(menu_category_keys);i++){if(i>=2){gboolean populated=FALSE;for(guint k=0;k<appdata->len;k++)if(!strcmp(application_group(g_ptr_array_index(appdata,k)),cats[i])){populated=TRUE;break;}if(!populated)continue;}GtkWidget*b=gtk_radio_button_new_with_label(group,labels[i]);group=gtk_radio_button_get_group(GTK_RADIO_BUTTON(b));gtk_toggle_button_set_mode(GTK_TOGGLE_BUTTON(b),FALSE);GtkWidget*category_label=gtk_bin_get_child(GTK_BIN(b));gtk_label_set_ellipsize(GTK_LABEL(category_label),PANGO_ELLIPSIZE_END);gtk_label_set_max_width_chars(GTK_LABEL(category_label),22);if(i==0)gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(b),TRUE);g_signal_connect(b,"toggled",G_CALLBACK(choose),(gpointer)cats[i]);gtk_box_pack_start(GTK_BOX(categories),b,FALSE,FALSE,1);}gsize custom_count=0;char **custom=g_key_file_get_string_list(menu_preferences,"Menu","CustomCategories",&custom_count,NULL);for(gsize i=0;i<custom_count;i++){char *key=g_strconcat("custom:",custom[i],NULL);gboolean populated=FALSE;for(guint k=0;k<appdata->len;k++)if(!strcmp(application_group(g_ptr_array_index(appdata,k)),key)){populated=TRUE;break;}if(!populated){g_free(key);continue;}GtkWidget*b=gtk_radio_button_new_with_label(group,custom[i]);group=gtk_radio_button_get_group(GTK_RADIO_BUTTON(b));gtk_toggle_button_set_mode(GTK_TOGGLE_BUTTON(b),FALSE);GtkWidget*category_label=gtk_bin_get_child(GTK_BIN(b));gtk_label_set_ellipsize(GTK_LABEL(category_label),PANGO_ELLIPSIZE_END);gtk_label_set_max_width_chars(GTK_LABEL(category_label),22);g_object_set_data_full(G_OBJECT(b),"category-key",key,g_free);g_signal_connect(b,"toggled",G_CALLBACK(choose),key);gtk_box_pack_start(GTK_BOX(categories),b,FALSE,FALSE,1);}g_strfreev(custom);GtkWidget*sc=gtk_scrolled_window_new(NULL,NULL);gtk_scrolled_window_set_policy(GTK_SCROLLED_WINDOW(sc),GTK_POLICY_NEVER,GTK_POLICY_ALWAYS);gtk_scrolled_window_set_overlay_scrolling(GTK_SCROLLED_WINDOW(sc),FALSE);gtk_scrolled_window_set_min_content_height(GTK_SCROLLED_WINDOW(sc),70);gtk_box_pack_start(GTK_BOX(body),sc,TRUE,TRUE,0);list=gtk_box_new(GTK_ORIENTATION_VERTICAL,2);gtk_container_add(GTK_CONTAINER(sc),list);GtkWidget*size_button=gtk_button_new_with_label("Menu Size & Spacing…");gtk_style_context_add_class(gtk_widget_get_style_context(size_button),"menu-size-button");gtk_button_set_image(GTK_BUTTON(size_button),gtk_image_new_from_icon_name("preferences-desktop-font",GTK_ICON_SIZE_BUTTON));gtk_button_set_always_show_image(GTK_BUTTON(size_button),TRUE);g_signal_connect(size_button,"clicked",G_CALLBACK(menu_size_dialog),NULL);GtkWidget*footer=gtk_box_new(GTK_ORIENTATION_HORIZONTAL,8);gtk_box_pack_start(GTK_BOX(outer),footer,FALSE,FALSE,0);gtk_box_pack_start(GTK_BOX(footer),size_button,TRUE,TRUE,0);GtkWidget*close=gtk_button_new_with_label("Close Menu  (Esc)");gtk_button_set_image(GTK_BUTTON(close),gtk_image_new_from_icon_name("window-close",GTK_ICON_SIZE_BUTTON));gtk_button_set_always_show_image(GTK_BUTTON(close),TRUE);gtk_style_context_add_class(gtk_widget_get_style_context(close),"menu-close");g_signal_connect(close,"clicked",G_CALLBACK(menu_close),NULL);gtk_box_pack_end(GTK_BOX(footer),close,TRUE,TRUE,0);g_signal_connect(searchbox,"changed",G_CALLBACK(changed),NULL);g_signal_connect(w,"key-press-event",G_CALLBACK(escape),NULL);g_signal_connect(w,"destroy",G_CALLBACK(menu_destroyed),NULL);
 g_signal_connect(w,"focus-out-event",G_CALLBACK(menu_focus_out),NULL);
 g_signal_connect(w,"focus-in-event",G_CALLBACK(menu_focus_in),NULL);
 fill();menu_apply_size();gtk_widget_show_all(w);gtk_widget_grab_focus(searchbox);}
/* Only the menu uses GtkApplication. The widgets, control-center and all
   standalone tools retain their original GTK startup and process behavior. */
static void menu_activated(GApplication*application,gpointer unused){
 (void)unused;
 if(menu_window){menu_close(NULL,NULL);return;}
 menu();
 gtk_application_add_window(GTK_APPLICATION(application),GTK_WINDOW(menu_window));
 gtk_window_present(GTK_WINDOW(menu_window));
}
static int run_menu_application(const char*program){
 GtkApplication*application=gtk_application_new("org.shadowrealm_os.ShadowLinkMenu",G_APPLICATION_DEFAULT_FLAGS);
 g_signal_connect(application,"activate",G_CALLBACK(menu_activated),NULL);
 char*av[]={(char*)program,NULL};
 int status=g_application_run(G_APPLICATION(application),1,av);
 g_object_unref(application);
 return status;
}
#include "extra-functions.c"
#include "desktop-utilities.c"
#include "desktop-extras.c"
static void application_data_dirs(void){
 const char *current=g_getenv("XDG_DATA_DIRS");
 char *all=g_strdup_printf("%s/.local/share/shadow-link/share:%s/.local/share/flatpak/exports/share:/var/lib/flatpak/exports/share:%s",g_get_home_dir(),g_get_home_dir(),current&&*current?current:"/usr/local/share:/usr/share");
 char **parts=g_strsplit(all,":",-1);GHashTable *seen=g_hash_table_new(g_str_hash,g_str_equal);GString *value=g_string_new(NULL);
 for(char **p=parts;*p;p++){if(!**p||g_hash_table_contains(seen,*p))continue;g_hash_table_add(seen,*p);if(value->len)g_string_append_c(value,':');g_string_append(value,*p);}
 g_setenv("XDG_DATA_DIRS",value->str,TRUE);g_string_free(value,TRUE);g_hash_table_destroy(seen);g_strfreev(parts);g_free(all);
}
static void process_role(int argc,char**argv){const char *name=(argc==1||!strcmp(argv[1],"--widgets"))?"Shadow Widgets":"Shadow Link";const char*pairs[][2]={{"--menu","Shadow Menu"},{"--control-center","Control Center"},{"--calendar","ShadowCalendar"},{"--clock","Shadow Clock"},{"--calculator","ShadowCalc"},{"--image-viewer","Shadow Viewer"},{"--media","Shadow Media"},{"--widget-settings","WidgetSettings"}};if(argc>1)for(guint i=0;i<G_N_ELEMENTS(pairs);i++)if(!strcmp(argv[1],pairs[i][0])){name=pairs[i][1];break;}prctl(PR_SET_NAME,name,0,0,0);}
int main(int argc,char**argv){process_role(argc,argv);application_data_dirs();self=argv[0];if(argc>1&&(!strcmp(argv[1],"--appearance")||!strcmp(argv[1],"--desktop-settings"))){char*p=g_build_filename(g_get_home_dir(),".local","share","shadow-link","bin","shadow-appearance",NULL);execl(p,p,!strcmp(argv[1],"--desktop-settings")?"--wallpapers":"--themes",NULL);perror("Appearance");return 1;}if(argc>1&&(!strcmp(argv[1],"--shield")||!strcmp(argv[1],"--network")||!strcmp(argv[1],"--bluetooth"))){char*p=g_build_filename(g_get_home_dir(),".local","share","shadow-link","bin","shadow-system-panels",NULL);execl("/usr/bin/python3","python3",p,argv[1],NULL);perror("Shadow settings");return 1;}if(argc>1&&!strcmp(argv[1],"--audio")){char*p=g_build_filename(g_get_home_dir(),".local","share","shadow-link","bin","shadow-audio-panel",NULL);execl("/usr/bin/python3","python3",p,NULL);perror("Shadow Audio");return 1;}if(argc>2&&!strcmp(argv[1],"--calculate")){double v;if(!calculate(argv[2],&v))return 2;printf("%.12g\n",v);return 0;}if(argc>1&&!strcmp(argv[1],"--fetch"))return fetch();if(argc>1&&!strcmp(argv[1],"--prepare-icons"))return prepare_icons();char*path=g_strdup_printf("%s/.local/share/shadow-link/bin:%s/.local/bin:%s",g_get_home_dir(),g_get_home_dir(),g_getenv("PATH")?g_getenv("PATH"):"/usr/bin:/bin");g_setenv("PATH",path,TRUE);g_free(path);appearance_read();gtk_init(&argc,&argv);brand=gdk_pixbuf_new_from_file_at_scale(basefile("logo.png"),24,24,TRUE,NULL);GtkCssProvider*css=gtk_css_provider_new();const char*home=g_get_home_dir();gchar *theme=NULL;g_object_get(gtk_settings_get_default(),"gtk-theme-name",&theme,NULL);char *p=g_build_filename(home,".themes",theme,"gtk-3.0","gtk.css",NULL);g_free(theme);if(g_file_test(p,G_FILE_TEST_IS_REGULAR))gtk_css_provider_load_from_path(css,p,NULL);g_free(p);gtk_style_context_add_provider_for_screen(gdk_screen_get_default(),GTK_STYLE_PROVIDER(css),GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);
 GtkCssProvider *accent_css=gtk_css_provider_new();
 gtk_css_provider_load_from_data(accent_css,
  ".shadow-app-heading, .shadow-clock-time { color: @theme_selected_bg_color; }"
  " .shadow-app-heading { font-size: x-large; font-weight: bold; }"
  " .shadow-clock-time { font-size: 30pt; font-weight: bold; }", -1,NULL);
 gtk_style_context_add_provider_for_screen(gdk_screen_get_default(),GTK_STYLE_PROVIDER(accent_css),GTK_STYLE_PROVIDER_PRIORITY_APPLICATION+1);
 g_object_unref(accent_css);g_signal_connect(gtk_settings_get_default(),"notify::gtk-theme-name",G_CALLBACK(appearance_css_changed),css);if(argc>1&&!strcmp(argv[1],"--notice")){GtkWidget*m=gtk_message_dialog_new(NULL,0,GTK_MESSAGE_INFO,GTK_BUTTONS_CLOSE,"%s",argc>2?argv[2]:"This component is not installed yet.");gtk_window_set_title(GTK_WINDOW(m),"Shadow Link");gtk_dialog_run(GTK_DIALOG(m));gtk_widget_destroy(m);return 0;}if(argc>1&&!strcmp(argv[1],"--network"))network_page();else if(argc>1&&!strcmp(argv[1],"--audio"))audio_page();else if(argc>1&&!strcmp(argv[1],"--bluetooth"))bluetooth_page();else if(argc>1&&!strcmp(argv[1],"--image-viewer")){g_spawn_command_line_async("/usr/bin/ristretto",NULL);return 0;}else if(argc>1&&!strcmp(argv[1],"--media")){g_spawn_command_line_async("/usr/bin/vlc",NULL);return 0;}else if(argc>1&&!strcmp(argv[1],"--calendar"))calendar_page();else if(argc>1&&!strcmp(argv[1],"--clock"))clock_page();else if(argc>1&&!strcmp(argv[1],"--calculator"))calculator();else if(argc>1&&!strcmp(argv[1],"--widget-settings"))widget_settings();else if(argc>1&&!strcmp(argv[1],"--control-center"))controls();else if(argc>1&&!strcmp(argv[1],"--shield"))shield();else if(argc>1&&!strcmp(argv[1],"--menu"))return run_menu_application(argv[0]);else widgets();gtk_main();return 0;}


static void reload_transparency(GFileMonitor *monitor,GFile *file,GFile *other,
                                GFileMonitorEvent event,gpointer data)
{
    (void)monitor;(void)file;(void)other;(void)event;
    char *path=g_build_filename(g_get_home_dir(),".config","shadowrealm-os","transparency.css",NULL);
    if(g_file_test(path,G_FILE_TEST_IS_REGULAR))
        gtk_css_provider_load_from_path(GTK_CSS_PROVIDER(data),path,NULL);
    g_free(path);
}
static void setting_window_visual(GtkWidget *window)
{
    static GFileMonitor *monitor;
    static GtkCssProvider *provider;
    gtk_widget_set_name(window,"shadow-settings-window");
    if(!provider){
        provider=gtk_css_provider_new();
        char *path=g_build_filename(g_get_home_dir(),".config","shadowrealm-os",NULL);
        GFile *directory=g_file_new_for_path(path);
        monitor=g_file_monitor_directory(directory,G_FILE_MONITOR_WATCH_MOVES,NULL,NULL);
        if(monitor)g_signal_connect(monitor,"changed",G_CALLBACK(reload_transparency),provider);
        g_object_unref(directory);g_free(path);
        reload_transparency(NULL,NULL,NULL,0,provider);
        gtk_style_context_add_provider_for_screen(gtk_widget_get_screen(window),
            GTK_STYLE_PROVIDER(provider),GTK_STYLE_PROVIDER_PRIORITY_USER);
    }
    GdkScreen *screen = gtk_widget_get_screen(window);
    GdkVisual *visual = gdk_screen_get_rgba_visual(screen);
    if (visual)
        gtk_widget_set_visual(window, visual);
}
