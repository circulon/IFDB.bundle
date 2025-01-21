IFDB.bundle
=============

A Plex metadata agent for scraping information from the Internet Fanedit Database (IFDB).

This is an extensive rewrite based on the original (https://github.com/tomfin46/IFDB.bundle) which no longer works.

A big thanks to ZeroQI for the amazing work on the HAMA.bundle (https://github.com/ZeroQI/Hama.bundle) 
which I used a couyple of common claases from... cheers

Issues should be created here: https://github.com/circulon/IFDB.bundle/issues

### Installation
#### Plex Support articles
- Finding the Plug-ins folder: https://support.plex.tv/articles/201106098-how-do-i-find-the-plug-ins-folder/
- Manually installing Plug-ibs: https://support.plex.tv/articles/201187656-how-do-i-manually-install-a-plugin/

#### Docker containers
If your using a docker container you should sheck the Path or Volume vars for `/config` or `/appdata` container paths.
NOTE: The above paths are the more common names but might be different in your container.
The Host path mapping will contain your start point (Library) to navigate to the `Plug-ins` folder

#### Installing the Plug-in
These steps are intentionally general as PMS runs on so many platforms its impossible to cover them all

##### Steps:
- Find the `Plug-ins` folder on your PMS system (Use the Plex Support articles above).
- Install the IFDB Plug-in via one of the following methods:
  - ****Option 1**: From a zip file** 
    - get the latest code from [here](https://github.com/circulon/IFDB.bundle/archive/refs/heads/master.zip) 
    - extract it and rename the extracted folder `master` to `IFDB.bundle`
    - copy/move the `IFDB.bundle` folder to the `Plugins-ins` folder you found above
  - **Option 2: Clone the git repo**
    - cd to the `Pkug-ins` folder you found above
    - `git clone https://github.com/circulon/IFDB.bundle.git`
- Fix permissions on the `IFDB.bundle` folder (optional)
- Retsrt the Plex server

#### Post Installatio Checks
Once installation is complete 
- Open your Plex interface (app/browser)
- Navigate to `Settings-><your Plex server>->Agents (Legacy)`
- Under the `Movies` section you should see the `IFDB Movies` agent.
- Installation is now verified and you can use this agent for individual item searches or as a Library default Agent.

### Metadata field alignments
TODO
