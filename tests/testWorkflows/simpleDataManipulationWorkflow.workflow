<?xml version="1.0"?>
<workflow name="helloWorldWorkflow">
    <options>
        <enabled>true</enabled>
        <scheduler type="cron" autorun="false">
            <month>1-2</month>
            <day>*</day>
            <hour>*</hour>
            <second>*/10</second>
        </scheduler>
    </options>
    <steps>
        <step id="start">
            <action>repeatBackToMe</action>
            <app>HelloWorld</app>
            <device>hwTest</device>
            <input>
                <call>Hello World</call>
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
    </steps>
</workflow>
