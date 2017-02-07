<?xml version="1.0"?>
<workflows>
    <workflow name="parentWorkflow">
        <options>
            <enabled>true</enabled>
            <children>
                <child>childWorkflow</child>
            </children>
            <scheduler type="cron" autorun="false">
                <month>11-12</month>
                <day>*</day>
                <hour>*</hour>
                <minute>*/0.1</minute>
            </scheduler>
        </options>
        <steps>
            <step id="start">
                <action>repeatBackToMe</action>
                <app>HelloWorld</app>
                <device>hwTest</device>
                <input>
                    <call format="str">Parent Step One</call>
                </input>
                <next step="@childWorkflow:start:1">
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
                    <call format="str">Parent Step Two</call>
                </input>
                <next></next>
                <error></error>
            </step>
        </steps>
    </workflow>
    <workflow name="childWorkflow">
        <options>
            <enabled>true</enabled>
            <scheduler>
                <autorun>true</autorun>
                <sDT>2016-1-1 12:00:00</sDT>
                <interval>0.1</interval>
                <eDT>2016-3-15 12:00:00</eDT>
            </scheduler>
        </options>
        <steps>
            <step id="start">
                <action>repeatBackToMe</action>
                <app>HelloWorld</app>
                <device>hwTest</device>
                <input>
                    <call format="str">Child Step One</call>
                </input>
                <next></next>
                <error></error>
            </step>
        </steps>
    </workflow>
</workflows>

