# Using the desktop

Open the application menu at the upper left. Categories group programs by purpose; favorites and dock entries can be edited. Third-party applications keep their own names and icons. Desktop right-click actions create folders, documents and launchers; Trash uses the normal desktop file services.

## Appearance

Use Control Center → Appearance to choose a coordinated style: Neon, Hacker, Red & Black, Woodland, White, Silver & Gold, Black & Blue, Black & White or Professional. Wallpaper selection is separate, so changing a picture does not silently change the whole style. Terminal, widget and menu background transparency controls affect supported backgrounds; application text and controls remain readable. Some third-party applications draw their own interface and may not follow every GTK setting.

## Applications and updates

Software tools expose installed applications and available packages. Debian applications are managed with APT; Flatpak applications use Flatpak. Updates need a working network connection. Read the operation summary before removing packages.

Debian and vendor repositories update their respective packages. The revised Beta 1 image includes the signed ShadowRealm-OS repository for custom desktop components and games. Open Software & Updates, refresh the package lists, review the offered updates and choose what to install. Flatpak updates are managed separately. The earlier Beta 1 image needs the one-time setup package described in [update repository](update-repository.md).

## Network and privacy

Network controls manage connections and custom DNS. Shadow Shield groups security controls. DNSCrypt encrypts DNS traffic to a compatible resolver; it is not a VPN and does not hide all traffic. Running its service does not, by itself, select it as the connection's DNS mode.

VPN support includes NetworkManager plugins and OpenVPN/WireGuard tools. A working VPN still needs a provider or server configuration and credentials. No VPN subscription or account is included. Tor Browser and the Tor service are different: the browser isolates and routes its own browsing traffic; starting the Tor service does not route every application through Tor. Tor Browser Launcher needs the internet for the browser download.

Internet pause/airplane controls can disconnect your session. The firewall starts with inbound connections restricted and allows users to manage explicit rules. There is no hidden, undeletable administrator SSH exception. Do not open ports you do not need.

## Accounts

Installed users choose their own password during installation. Sudo normally asks for the current user's password when that user is allowed to administer the system. Account changes requiring administrator authorization use a local prompt. Keep a backup before renaming a login and its Home directory; third-party application files may contain paths the system cannot safely rewrite.

## Games

The Games category contains the Linux games. They run offline without accounts or ads and keep local settings/high scores. Each game can be removed separately. 

## Login picture, background and sounds

In **User Account**, Choose Login Picture changes both the account preview and the login picture. Fresh accounts use the SR logo. The password and login/Home rename controls remain separate.

Open **Login, Sounds & Screensaver** in Control Center or Settings. Choose Login Background installs a separate system login image after administrator authentication. Use Theme Background removes that override so the selected desktop theme supplies it again. This setting changes the greeter, not your desktop wallpaper.

Sign-in and sign-out/shutdown chimes are optional, original synthesized sounds. Their volume control follows the system output and mute; Preview Sign-in Chime lets you check it. The sign-out sound requires an active desktop audio session and is not a firmware/power-off sound.

Choose Bouncing SR logo, Circuit flow or ShadowRealm-OS digital rain, then use Screensaver Timeout, Enable & Lock Settings to control idle activation and password locking. The default is a ten-minute idle timeout with locking enabled. Mouse or keyboard activity wakes the saver; enter your password if locking is enabled.

**Alarms & Timers** in Shadow Clock opens GNOME Clocks, which also has world clocks and a stopwatch. Keep the application/session running for alarms and timers; they do not power on a shut-down computer. Its standard alarm and timer sounds are included. Additional original sound files are supplied in the media collection.

**Drawing**, under Graphics, is the lightweight paint application. Its own Help explains the tools.

Click the top-bar time to open Clocks, with world clocks, alarms, timers and a stopwatch. The application-menu entry opens the same app.
