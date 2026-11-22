# MCXboxBroadcast

This add-on broadcasts an existing Geyser/Bedrock server over the Xbox Live network. This makes the server appear in the friends list of Xbox Live friends and allows them to join directly.

Based on the [MCXboxBroadcast Standalone Tool](https://github.com/MCXboxBroadcast/Broadcaster).

## Setup & Authentication

1.  Start the add-on.
2.  Open the **Log** tab of the add-on.
3.  Look for a message similar to this:
    `To sign in, use a web browser to open the page https://www.microsoft.com/link and enter the code XXXXXXXX to authenticate.`
4.  Open the link, enter the code, and log in with the Xbox account that will act as the "host".
5.  After a successful login, the add-on persists the token in the `/data/cache` directory. You usually do not need to log in again after a restart.

**Note:** It is highly recommended to use a secondary account (alt account) for this purpose to protect your main account.

## Configuration

Configuration is handled via the **Configuration** tab in the Add-on Store.

### Server Details
* **remote_address**: The IP or domain of your Geyser server (e.g., `192.168.1.50` or `geyser.myserver.com`). If set to `auto`, the tool attempts to determine the IP itself.
* **remote_port**: The port of your Bedrock server (default: `19132`).
* **host_name**: The text displayed as "Server Name" in the friends list.
* **world_name**: The "MotD" or world description.
* **max_players**: The maximum player count displayed.

### Update Intervals
* **update_interval**: How often (in seconds) the session status is sent to Xbox Live (min. 30 recommended).

### Friend Sync
Automated management of the bot account's friends list.

* **enabled**: Enables/Disables the module.
* **auto_follow**: Automatically follows players back when they add the bot.
* **auto_unfollow**: Unfollows players when they remove the bot.
* **initial_invite**: Sends a game invite immediately after a friend is added.

## Custom Image (Screenshot)

You can set a custom thumbnail for the Xbox list.

1.  Create an image with dimensions **1200x675** (JPG recommended).
2.  Name it `screenshot.jpg`.
3.  Upload it to the add-on's data directory. Since Home Assistant does not have a direct file browser for add-on data, you need to place it via SSH/Samba into the corresponding Docker volume path or (if configured) into the `addon_configs` folder.
    * Alternative: If you have access to the host file system, it is usually located at `/usr/share/hassio/addons/data/<slug>`.
4.  Restart the add-on.

It may take a few minutes for Xbox Live to update the image.

## Troubleshooting

* **Auth-Loop**: If the add-on constantly asks for a code, delete the cache folder and restart.
* **Cannot Join**: Ensure that `remote_port` allows UDP traffic and correctly points to the Geyser server. Since the add-on runs in the `host` network, there should be no Docker NAT issues.