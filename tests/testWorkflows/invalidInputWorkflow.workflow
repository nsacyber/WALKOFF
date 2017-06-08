<?xml version="1.0"?>
<workflow name="multiactionWorkflow">
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
            <next step="1">
                <flag action="regMatch">
                    <args>
                        <regex>(.*)</regex>
                    </args>
                    <filters>
                        <filter action="length">
                            <args></args>
                        </filter>
                    </filters>
                </flag>
            </next>
            <error></error>
        </step>
        <step id="1">
            <action>returnPlusOne</action>
            <app>Invalid</app>
            <device>hwTest</device>
            <inputs>
                <number>abc</number>
            </inputs>
            <next></next>
            <error></error>
        </step>
    </steps>
</workflow>
