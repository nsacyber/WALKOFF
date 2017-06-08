<?xml version="1.0"?>
<workflow name="templatedWorkflow" >
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
            <error step="1"></error>
        </step>
        <step id="1">
            <action>repeatBackToMe</action>
            <app>HelloWorld</app>
            <device>hwTest</device>
            <input>
                <call>{{outputFrom(steps, -1)}}</call>
            </input>
            <next>
            </next>
            <error step="1"></error>
        </step>
    </steps>
</workflow>
