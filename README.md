[![Build Status](https://travis-ci.org/iadgov/WALKOFF.svg?branch=master)](https://travis-ci.org/iadgov/WALKOFF)

<img src="https://iadgov.github.io/WALKOFF/files/images/flyingLogoWithTextSmall.png">
## Summary
WALKOFF is an open source automation platform that enables users to easily integrate, automate and customize their processes enabling their environment to automatically adapt and respond to security threats.   

## Description
WALKOFF is an automation platform enabling plug and play integration of devices through apps.  By employing an app based architecture, integration capabilities only need to be written once and can be swapped in and out as needed. 

Capabilities within WALKOFF apps can then be tied together to form Workflows.  Workflows are defined in an XML format making them easily sharable across environments and organizations.  

Apps can also have custom interfaces enabling app developers to uniquely display information.  WALKOFF not only makes it easier for users to automate their work but to also quickly find and visualize information as well.

Walkoff apps can be found at: https://github.com/iadgov/WALKOFF-Apps

## Features 
1. Custom app interfaces
    *  Interfaces are built using HTML/CSS/Javascript with back-end functionality using Python. 

    *  Capability to stream data to interfaces.

2. User and Role based authentication
  
3. Case based logging 
    * Can granularly configure which events to log on a per-case basis

4. Drag and Drop Workflow Editor
    * Makes creation and editing of workflows as easy as dragging and dropping capabilities.
    
5. Flexible Workflow Execution
    * Manual Execution - Execute a workflow by pressing a button
    * Active Execution - Cron style workflow execution
    
        *Run workflow every 8 hours for the next 3 months*
    
    * Passive Execution - Trigger a workflow based upon data sent to Walkoff
    
    * Ability to pause and resume workflows enabling *human in the loop* execution

7. Metrics
    *How often are certain apps run? 
    
    *How often workflows are run? 
    
## Base Requirements
Python 2.7+ or Python 3.4+
NodeJS and Node Package Manager (npm)
Tested on Windows and Linux 

*Requirements for apps may differ* 

## Installation Instructions
You can run (possibly with administrator privileges)
   `python make.py`

Alternatively, you can manually install

First, install the dependencies with the following command:

   `pip install -r requirements.txt`
   
To install the dependencies for each individual app, run:

   `python installDependencies.py`
   
Or to just install the dependencies for specific apps:

   `python installDependencies -a AppOne,AppTwo,AppThree`

Next, navigate to /client and install the client dependencies with the following commands:

   `npm install`
   `npm install gulp-cli -g` (If you need to install gulp)

Next, use gulp to build the client:

   `gulp ts`

That's it! To start up the server, just navigate back to the walkoff root and run:

   `python startServer.py` 
   
Then, navigate to the specified IP and port to start using WALKOFF. The default is http://127.0.0.1:5000.

## Apps
WALKOFF-enabled apps can be found at www.github.com/iadgov/walkoff-apps

## Branches
1. Master - Main branch for WALKOFF version 2 will be updated from development periodically
2. Development - Development branch for WALKOFF version 2.  Updated frequently
3. Walkoff-Experimental - WALKOFF version 1  *No longer under development*

*Other development-centric branches may be created but should not be considered permanent* 

## Stability and Versioning
Walkoff is still under active development; as such, changes are being made frequently to the code base as new features
are added. We are using Semantic Versioning. Until the full feature set is developed, the versions will begin with 0.x.y
The "x" version will be updated when a breaking change is made, a breaking change being defined as one which modifies
either a database schema or the REST API or a new method in which way in which apps are developed and specified which
is not backward-compatible with the previous version. No guarantees are yet made for the stability of the backend
Python modules. The "y" version will be updated for patches, bug fixes, and non-breaking features.

## Contributions
WALKOFF is a community focused effort and contributions are welcome.  

Comments or questions?  walkoff@nsa.gov 
