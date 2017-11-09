[![Build Status](https://travis-ci.org/iadgov/WALKOFF.svg?branch=master)](https://travis-ci.org/iadgov/WALKOFF)

<img src="https://iadgov.github.io/WALKOFF/files/images/flyingLogoWithTextSmall.png">

# Description

* Are repetitive, tedious processes taking up too much of your time?
* Is more time spent focusing on managing your data than acting on the data
  itself?

WALKOFF is an automation framework that allows you to easily automate these 80%
of tedious tasks so you can get the job done faster, easier, and cheaper.

WALKOFF is built upon an app based architecture which enables the plug and play
integration of devices and capabilities.  These capabilities can then be tied
together to form Workflows.  Workflows are defined in a JSON format making them
easily sharable across environments and organizations and easily
created/customizable through our drag and drop workflow editor.

<center><img src="https://raw.githubusercontent.com/iadgov/WALKOFF/gh-pages/files/images/demoGIFs/DragDropGIF.gif" height=300></center>

WALKOFF also makes it easier to manage your newly automated processes with
real-time visual updates and feeds based on your workflows progress.

<img src="https://raw.githubusercontent.com/iadgov/WALKOFF/gh-pages/files/images/demoGIFs/realTimeUpdates.gif" height=300>

Apps can also have custom interfaces enabling app developers to uniquely
display information.  WALKOFF not only makes it easier for users to automate
their processes but allows users to act on their processes faster as well.

<img src="https://raw.githubusercontent.com/iadgov/WALKOFF/gh-pages/files/images/demoGIFs/customAnalytics.gif" height=300>

Walkoff apps can be found at: <https://github.com/iadgov/WALKOFF-Apps>

## Installation Instructions

To install, you can run (possibly with administrator privileges)
   `python make.py`

Alternatively, you can manually install WALKOFF

First, install the dependencies with the following command:

   `pip install -r requirements.txt`

To install the dependencies for each individual app, run:

   `python installDependencies.py`

Or to just install the dependencies for specific apps:

   `python installDependencies -a AppOne,AppTwo,AppThree`

Next, navigate to /client and install the client dependencies with the
following commands:

   `npm install`
   `npm install gulp-cli -g` (If you need to install gulp)

Next, use gulp to build the client:

   `gulp ts`

That's it! To start up the server, just navigate back to the walkoff root and
run:

   `python startServer.py`

Then, navigate to the specified IP and port to start using WALKOFF. The default
is `http://127.0.0.1:5000`.

## Features

1. Custom app interfaces
   * Interfaces are built using HTML/CSS/Javascript with back-end
     functionality using Python.

   * Capability to stream data to interfaces.

2. User and Role based authentication

3. Case based logging
   * Can granularly configure which events to log on a per-case basis

4. Drag and Drop Workflow Editor
   * Makes creation and editing of workflows as easy as dragging and dropping
     capabilities.

5. Flexible Workflow Execution
   * Manual Execution - Execute a workflow by pressing a button
   * Active Execution - Cron style workflow execution
     *Run workflow every 8 hours for the next 3 months*
   * Passive Execution - Trigger a workflow based upon data sent to Walkoff
   * Ability to pause and resume workflows enabling *human in the loop*
     execution

6. Metrics
   * How often are certain apps run?

   * How often workflows are run?

## Base Requirements

* Python 2.7+ or Python 3.4+
* NodeJS and Node Package Manager (npm)
* Tested on Windows and Linux

*Requirements for apps may differ*

## Apps

WALKOFF-enabled apps can be found at www.github.com/iadgov/walkoff-apps

## Branches

1. Master - Main branch for WALKOFF version 2 will be updated from development
   periodically
2. Development - Development branch for WALKOFF version 2.  Updated frequently
3. Walkoff-Experimental - WALKOFF version 1  *No longer under development*

*Other development-centric branches may be created but should not be
considered permanent*

## Stability and Versioning

WALKOFF uses Semantic Versioning. Until the full feature set is developed, the
versions will begin with 0.x.y. The "x" version will be updated when a breaking
change is made, a breaking change being defined as one which modifies either a
database schema, the REST API, the workflow format, or API used to develop and
specify the apps is modified in a way which breaks backward compatibility. No
guarantees are yet made for the stability of the backend Python modules. The
"y" version will be updated for patches, bug fixes, and non-breaking features.

## Contributions

WALKOFF is a community focused effort and contributions are welcome.

Comments or questions?  walkoff@nsa.gov
