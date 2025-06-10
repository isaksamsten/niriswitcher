# niriswitcher

An application switcher for niri, with support for workspaces and automatic light and dark mode.
![Image](https://github.com/user-attachments/assets/33ad582f-4540-428a-8fbc-849c35c7ec76)

## Features

- Fast, beautiful application switching for [niri](https://github.com/YaLTeR/niri)
- Workspace-aware: switch apps in current or all workspaces
- Automatic light/dark mode with easy theming via CSS
- Customizable keybindings and appearance (icon size, window width, animation)
- MRU sorting and smooth animations

## Screencast

https://github.com/user-attachments/assets/81beb414-6367-4d6f-aa2b-9c55534913b3

## Installation

### pipx

To install the development version use:

```bash
pipx install --system-site-packages git+https://github.com/isaksamsten/niriswitcher.git
```

append `@tag`, where tag is a tagged version number, e.g., `0.1.2`, to the url
to install a release version.

> [!NOTE]
> You must use `--system-site-packages` to avoid having to build `pygobjects` from source.
> You also need to install the following system packages:
>
> - `python3-gobject`
> - `gtk4-layer-shell`
> - `libadwaita`
>
> These are the names of the packages on Fedora, but I'm sure they are
> distributed for other distributions.

### Fedora

For users of Fedora, I maintain a COPR built for every release.

[![Copr build status](https://copr.fedorainfracloud.org/coprs/isaksamsten/niriswitcher/package/niriswitcher/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/isaksamsten/niriswitcher/package/niriswitcher/)

```bash
dnf copr enable isaksamsten/niriswitcher
dnf install niriswitcher
```

### Arch-based distributions

niriswitcher is now available in the AUR. You can use any of your AUR helpers to install.

```bash
yay -S niriswitcher
```

### Nix

A [Nix package](https://search.nixos.org/packages?channel=unstable&show=niriswitcher) for niriswitcher is available. Add the following to your configuration:

```nix
environment.systemPackages = with pkgs; [
  niriswitcher
];
```

A [home-manager module](https://nix-community.github.io/home-manager/options.xhtml#opt-programs.niriswitcher.enable) is also available.

## Configuration

First we need to execute the `niriswitcher` application. The program is
deamonized and waits for `USR1` signal to be shown. In the niri
`config.kdl`-file we first start `niriswitcher` at startup:

```kdl
spawn-at-startup "niriswitcher"
```

> [!NOTE]
> Replace `niriswitcher` with `~/.local/bin/niriswitcher` if you installed using `pipx` and the binary is not on `$PATH`

Next, we add keybindings to send the `USR1` signal to `niriswitcher` on `Alt+Tab` and `Alt+Shift+Tab`.

> [!NOTE]
> Remember to synchronize the keybinding set in Niri, with the one set for `niriswitcher`. For example, if you use `Mod+Tab` to trigger `niriswitcher` ensure that `modifier=Mod` in `config.toml`.

You can either use `niriswitcherctl`, `USR1` signal (deprecated) or direct DBus
calls to trigger `niriswitcher`.

### niriswitcherctl

Due to Python's slow startup time, this method introduces a slight delay of a few milliseconds (generally unnoticeable, but it increases the chance that `niriswitcher` may not be dismissed upon `Alt` release)

```kdl
bind {
    Alt+Tab repeat=false { spawn "niriswitcherctl" "show" "--window"; }
    Alt+Shift+Tab repeat=false { spawn "niriswitcherctl" "show" "--window"; }
    Alt+Grave repeat=false { spawn "niriswitcherctl" "show" "--workspace"; }
    Alt+Shift+Grave repeat=false { spawn "niriswitcherctl" "show" "--workspace"; }
}
```

### gdbus

This is generally a few milliseconds faster than `niriswitcherctl`.

```kdl
    Alt+Tab repeat=false { spawn "gdbus" "call" "--session" "--dest" "io.github.isaksamsten.Niriswitcher" "--object-path" "/io/github/isaksamsten/Niriswitcher" "--method" "io.github.isaksamsten.Niriswitcher.application" ; }
    Alt+Shift+Tab repeat=false { spawn "gdbus" "call" "--session" "--dest" "io.github.isaksamsten.Niriswitcher" "--object-path" "/io/github/isaksamsten/Niriswitcher" "--method" "io.github.isaksamsten.Niriswitcher.application" ; }
```

Change `.application` to `.workspace` if you want to bind "next application in
most recently used workspace"

### pkill

> [!WARNING]
> Using `USR1` to trigger `niriswitcher` has been deprecated in favour of DBus,

```kdl
bind {
    Alt+Tab repeat=false { spawn "pkill" "-USR1" "niriswitcher"; }
    Alt+Shift+Tab repeat=false { spawn "pkill" "-USR1" "niriswitcher"; }
}
```

### Keybindings

By default, `niriswitcher` uses the following keybindings:

- `Alt+Tab` select next application
- `Alt+Shift+Tab` select previous application
- `Alt+Esc` close `niriswitcher` and do not focus
- `Alt+q` to close the selected application
- ``Alt+` `` to show the next workspace
- ``Alt+Shift+` `` to show the previous workspace

- Release `Alt` to focus to currently selected application and close `niriswitcher`

The default mappings and modifier key can be configured in the `config.toml` file.

### Options

`niriswitcher` has a few options that we can change

- The icon size
- The maximum width of the switcher window (before scrolling)
- The scroll animation speed (set to 0 to disable)
- If single click change application without hiding the switcher (double
  clicking an application changes focus and hides the switcher)
- If `separate_workspaces` is set to `true`, the application switcher will
  show windows from the current workspace and enable workspace navigation. If
  `false`, the switcher will show applications from all workspaces and disable
  workspace navigation.
- Sort order of workspaces in the switcher.
  - If `workspace.mru_sort_in_workspace` is set to `true` the workspaces are sorted in
    order of last used when started with the most recently used window; otherwise
    in order of their workspace index (as in Niri moving up and down).
  - If `workspace.mru_sort_across_workspace` is set to `true` workspaces are sorted in
    order of last used when started with the most recently used window from the
    most recently used workspace; otherwise in order of workspace index.
- Workspace name format in the switcher is controlled by `workspace_format`.
  The format string supports `{name}`, `{output}` and `{idx}`.

The configuration file is a simple `.toml`-file in
`$XDG_CONFIG_HOME/niriswitcher/config.toml`. This is the default configuration:

```toml
separate_workspaces = true
double_click_to_hide = false
center_on_focus = false
log_level = "WARN"

[appearance]
icon_size = 128
max_width = 800
min_width = 600
system_theme = "dark" # auto or light
workspace_format = "{output}-{idx}" # {output}, {idx}, {name}

[workspace]
mru_sort_in_workspace = false
mru_sort_across_workspace = true

[appearance.animation.reveal]
hide_duration = 200
show_duration = 200
easing = "ease-out-cubic"

[appearance.animation.resize]
duration = 200
easing = "ease-in-out-cubic"

[appearance.animation.workspace]
duration = 200
transition = "slide"

[appearance.animation.switch]
duration = 200
easing = "ease-out-cubic"

[keys]
modifier = "Alt_L"

[keys.switch]
next = "Tab"
prev = "Shift+Tab"

[keys.window]
close = "q"
abort = "Escape"

[keys.workspace]
next = "grave"
prev = "Shift+asciitilde"
```

The `modifier` key keeps `niriswitcher` active (once released, `niriswitcher`
is closed and the selected application activated). It's implicitly part of the
other key mappings, so in the default configuration `Alt+Tab` moves to the next
application, `Alt+Shift+Tab` to the previous, and so forth. To change the
modifier key, select another key among: `Alt`, `Super`, `Shift`, or `Control`.

The other bindings are expressed as bindings, e.g.,
`Shift+Tab` or `Control+j`. Note that `modifier` is implicit in all
bindings.

> [!WARNING]
> When using `Mod` or `Super` as the `modifier`, `niri` seems to inhibit
> `Super+Escape` reaching `niriswitcher`. Please select another binding for
> `abort`.

### Themes

We can also change/improve the style of the switcher using a `style.css` file
in the same configuration directory.

The following CSS can be styled:

- `#niriswitcher`: the main window
- `#application-title`: the title (above the icons)
- `#workspace-name`: the workspace name (above the icons)
- `#workspaces`: the workspace area
- `.workspace`: a workspace in the workspace area (contains the icons)
- `#workspace-indicators`: the workspace indicator area
- `.workspace-indicator`: the workspace indicator
- `.workspace-indicator.selected`: the currently selected workspace indicator
- `.application-icon`: the icon
- `.application-name`: the application name (below the icon)
- `.application-strip`: the area behind the icons (inside the scroll)
- `.application`: the application area (name + icon)
- `.application.selected`: the currently selected application (by keyboard or mouse)

Example (see `./src/niriswitcher/resources/style.css` for the default config):

To make the application title and selected application name red.

```css
.application-title {
  color: red;
}
.application.selected .application-name {
  color: red;
}
```

To make the application name visible for non-selected applications (but dimmed):

```css
.application-name {
  opacity: 1;
  color: rgba(255, 255, 255, 0.6);
}
.application.selected .application-name {
  color: rgba(255, 255, 255, 1);
}
```

To hide the window title and workspace name:

```css
#top-bar {
  opacity: 0;
}
```

To hide the workspace name:

```css
#workspace-name {
  opacity: 0;
}
```

`niriswitcher` also uses `style-dark.css` to style the application in `dark` mode.

If you only want to change the colors, you only need to override the colors
(these are the default colors in light mode, see `style-dark.css` in the
resources folder for default colors in dark mode):

```css
:root {
  --bg-color: rgba(229, 229, 234, 1);
  --label-color: rgb(58, 58, 60);
  --alternate-label-color: rgb(44, 44, 46);
  --dim-label-color: rgb(142, 142, 147);
  --border-color: rgba(199, 199, 204, 0.95);
  --highlight-color: rgba(209, 209, 214, 0.95);
  --urgency-color: rgb(255, 69, 58);
  --indicator-focus-color: rgba(10, 132, 255, 0.95);
  --indicator-color: rgba(209, 209, 214, 0.95);
}
```

#### Default light mode style

![Image](https://github.com/user-attachments/assets/10593e6a-53d7-4359-951d-59270088bbc6)

#### Default dark mode style

![Image](https://github.com/user-attachments/assets/33ad582f-4540-428a-8fbc-849c35c7ec76)

[Input on the default design is welcome](https://github.com/isaksamsten/niriswitcher/issues/8)

## Known issues

If `Alt` (the modifier key) is released before `niriswitcher` has been fully initialized, the window will not close unless the modifier key is pressed and released (to change to the next application) or `Esc` is pressed to close the window.
