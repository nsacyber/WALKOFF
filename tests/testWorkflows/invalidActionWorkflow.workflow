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
            <action>invalid</action>
            <app>HelloWorld</app>
            <device>hwTest</device>
            <input>
            </input>
            <next step="1">
                <flag action="regMatch">
                    <args>
                        <regex format="str">(.*)</regex>
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
            <action>repeatBackToMe</action>
            <app>HelloWorld</app>
            <device>hwTest</device>
            <input>
                <call format="str">Hello World</call>
            </input>
            <next></next>
            <error></error>
        </step>
    </steps>
</workflow>
