[![Build Status](https://travis-ci.org/iadgov/WALKOFF.svg?branch=master)](https://travis-ci.org/iadgov/WALKOFF)
# WALKOFF
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
    * Makes creation and editing of workflows as easy as dragging and dropping capablities. 
    
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
Tested on Windows and Linux 

*Requirements for apps may differ* 

## Installation Instructions
First, install the dependencies with the following command:

   `pip install -r requirements.txt`
   
To install the dependencies for each individual app, run:

   `python installDependencies.py`
   
Or to just install the dependencies for specific apps:

   `python installDependencies -a AppOne,AppTwo,AppThree`

That's it! To start up the server, just run:

   `python startServer.py` 
   
Then, navigate to the specified IP and port to start using WALKOFF. The default is http://127.0.0.1:5000.

## Apps
WALKOFF-enabled apps can be found at www.github.com/iadgov/walkoff-apps

## Branches
1. Master - Main branch for WALKOFF version 2 will be updated from development periodically
2. Development - Development branch for WALKOFF version 2.  Updated frequently
3. Walkoff-Experimental - WALKOFF version 1  *No longer under development*

*Other development-centric branches may be created but should not be considered permanent* 

## Contributions
WALKOFF is a community focused effort and contributions are welcome.  

Comments or questions?  walkoff@nsa.gov 
