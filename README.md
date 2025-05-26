# niriswitcher

An application switcher for niri, with support for workspaces and automatic light and dark mode.
![Image](https://github.com/user-attachments/assets/33ad582f-4540-428a-8fbc-849c35c7ec76)

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

niriswitcher is also available on NUR. Nix users can setup NUR by following [this](https://nur.nix-community.org/documentation) guide, but a short summary is provided below.

> [!NOTE]
> NUR packages are built against Nixpkgs unstable.

<details>

<summary>

#### With Flakes (without using Home Manager)

</summary>

For a simple flake based setup:

- Add NUR to your flake inputs
    ```nix
    nur = {
        url = "github:nix-community/NUR";
        inputs.nixpkgs.follows = "nixpkgs";
    };
    ```
- Add the NUR overlay to your NixOS configuration (optional)
    ```nix
    {
        nixpkgs.overlays = [ nur.overlays.default ];
    }
    ```
- To your packages list, add:
    - `pkgs.nur.repos.Vortriz.niriswitcher` if you added the overlay
    - `nur.legacyPackages."${pkgs.system}".repos.Vortriz.niriswitcher` if you did not use the overlay

</details>

<details>

<summary>

#### With Flakes (using Home Manager)

</summary>

- Add NUR to your flake inputs
    ```nix
    nur = {
        url = "github:nix-community/NUR";
        inputs.nixpkgs.follows = "nixpkgs";
    };
    ```
- Add `nur.legacyPackages."${pkgs.system}".repos.Vortriz.homeManagerModules.niriswitcher` to your `imports` in `home.nix`
- Set `programs.niriswitcher.enable = true`. Optionally, you can configure niriswitcher with `programs.niriswitcher.config` (for `config.toml`) and `programs.niriswitcher.style` (for `style.css`). The exact configuration values for these options are detailed in the section ahead.

For more information on using the module itself, check out the [source file](https://github.com/Vortriz/nur-packages/blob/main/modules/home-manager/niriswitcher.nix).
</details>

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

```kdl
bind {
    Alt+Tab repeat=false { spawn "pkill" "-USR1" "niriswitcher"; }
    Alt+Shift+Tab repeat=false { spawn "pkill" "-USR1" "niriswitcher"; }
}
```

> [!NOTE]
> Remember to synchronize the keybinding set in Niri, with the one set for `niriswitcher`. For example, if you use `Mod+Tab` to trigger `niriswitcher` ensure that `modifier=Mod` in `config.toml` (see below).

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
- If `separate_workspaces` is set to true, the application switcher will
  show windows from the current workspace and enable workspace navigation. If
  `false`, the switcher will show applications from all workspaces and disable
  workspace navigation.

The configuration file is a simple `.toml`-file in
`$XDG_CONFIG_HOME/niriswitcher/config.toml`. This is the default config:

```toml
separate_workspaces = true
double_click_to_hide = false
center_on_focus = false

[appearance]
icon_size = 128
max_width = 800
min_width = 600
system_theme = "dark" # auto or light

[appearance.animation.hide]
duration = 200
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
