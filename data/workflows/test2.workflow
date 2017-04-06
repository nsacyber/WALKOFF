<?xml version="1.0"?>
<workflow name="testingAnotherWorkflow">
    <options>
        <enabled>true</enabled>
        <scheduler type="cron" autorun="false">
            <month>11-12</month>
            <day>*</day>
            <hours>*</hours>
            <minutes>*/0.1</minutes>
        </scheduler>
    </options>
    <steps>
        <step id="start">
            <action>repeatBackToMe</action>
            <app>HelloWorld</app>
            <device>hwTest</device>
            <input>
                <call format="str">Hello World</call>
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
            <error step="1"></error>
        </step>
    </steps>
</workflow>
