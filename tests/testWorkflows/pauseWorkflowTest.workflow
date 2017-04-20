<?xml version="1.0"?>
<workflow name="pauseWorkflow">
    <options>
        <enabled>true</enabled>
        <scheduler type="cron" autorun="false">
            <month>11-12</month>
            <day>*</day>
            <hour>*</hour>
            <minute>*/0.1</minute>
        </scheduler>
    </options>
    <steps>
        <step id="start">
            <action>helloWorld</action>
            <app>HelloWorld</app>
            <device>hwTest</device>
            <input>
            </input>
            <next step="1"></next>
            <error></error>
        </step>
        <step id="1">
            <action>pause</action>
            <app>HelloWorld</app>
            <device>hwTest</device>
            <input>
                <seconds format="int">1</seconds>
            </input>
            <next step="really_unique_name"></next>
            <error></error>
        </step>
        <step id="really_unique_name">
            <action>pause</action>
            <app>HelloWorld</app>
            <device>hwTest</device>
            <input>
                <seconds format="int">1</seconds>
            </input>
            <next></next>
            <error></error>
        </step>
    </steps>
</workflow>
