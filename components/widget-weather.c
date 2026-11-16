static gchar *weather_location;
static gchar *weather_temperature;
static gchar *weather_condition;
static GSubprocess *weather_process;
static gint64 weather_next;
static gboolean weather_retry, weather_network_available;

static void weather_finished(GObject *source, GAsyncResult *result, gpointer unused)
{
    (void)unused;
    GSubprocess *process = G_SUBPROCESS(source);
    gchar *output = NULL;
    gboolean success = g_subprocess_communicate_utf8_finish(process, result, &output, NULL, NULL) &&
                       g_subprocess_get_successful(process);
    if (weather_process != process) {
        g_free(output);
        return;
    }
    g_clear_object(&weather_process);
    gboolean fresh = FALSE;
    if (success) {
        gchar **lines = g_strsplit(output, "\n", 4);
        if (lines[0] && lines[1]) {
            g_free(weather_temperature);
            weather_temperature = g_strdup(lines[0]);
            g_free(weather_condition);
            weather_condition = g_strdup(lines[1]);
            fresh = g_strcmp0(lines[2], "fresh") == 0;
        }
        g_strfreev(lines);
    } else {
        g_free(weather_condition);
        weather_condition = g_strdup(weather_temperature ? "Offline · cached forecast" : "Forecast unavailable");
    }
    weather_next = g_get_monotonic_time() +
                   (fresh ? 10800LL : 600LL) * G_USEC_PER_SEC;
    weather_retry = !fresh;
    g_free(output);
}

static void weather_update(gboolean enabled, double latitude, double longitude)
{
    gchar *location = NULL;
    if (enabled && isfinite(latitude) && isfinite(longitude) &&
        fabs(latitude) <= 90 && fabs(longitude) <= 180) {
        gchar lat[G_ASCII_DTOSTR_BUF_SIZE], lon[G_ASCII_DTOSTR_BUF_SIZE];
        g_ascii_formatd(lat, sizeof lat, "%.2f", latitude);
        g_ascii_formatd(lon, sizeof lon, "%.2f", longitude);
        location = g_strjoin(" ", lat, lon, NULL);
    }
    if (g_strcmp0(location, weather_location) != 0) {
        if (weather_process)
            g_subprocess_force_exit(weather_process);
        g_clear_object(&weather_process);
        g_clear_pointer(&weather_temperature, g_free);
        g_clear_pointer(&weather_condition, g_free);
        g_free(weather_location);
        weather_location = g_steal_pointer(&location);
        weather_next = 0;
        weather_retry = FALSE;
    }
    g_free(location);
    if (!weather_location)
        return;
    gboolean network_available = g_network_monitor_get_network_available(g_network_monitor_get_default());
    if (weather_retry && network_available && !weather_network_available)
        weather_next = 0;
    weather_network_available = network_available;
    if (weather_process || g_get_monotonic_time() < weather_next)
        return;

    gchar **coordinates = g_strsplit(weather_location, " ", 2);
    const gchar *script = "/usr/share/shadowrealm-os/desktop/runtime/bin/shadow-weather.py";
    weather_process = g_subprocess_new(G_SUBPROCESS_FLAGS_STDOUT_PIPE | G_SUBPROCESS_FLAGS_STDERR_SILENCE,
                                       NULL, "/usr/bin/python3", script, "--cache", "--card",
                                       coordinates[0], coordinates[1], NULL);
    g_strfreev(coordinates);
    if (weather_process)
        g_subprocess_communicate_utf8_async(weather_process, NULL, NULL, weather_finished, NULL);
    else
        weather_next = g_get_monotonic_time() + 600LL * G_USEC_PER_SEC;
}

static void draw_widget_weather(cairo_t *canvas)
{
    const gchar *fallback = weather_process ? "Fetching forecast…" :
                            weather_location ? "Forecast unavailable" : "Choose a location in Widget Settings";
    if (weather_temperature)
        txt(canvas, 16, 76, 26, weather_temperature, "f5e9ff", 1);
    txt(canvas, 16, 104, 10, weather_condition ? weather_condition : fallback, "f5e9ff", 0);
    txt(canvas, 16, 124, 10, "Forecast from MET Norway", "00eaff", 0);
}
