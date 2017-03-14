<?xml version="1.0"?>
<workflow name="helloWorldWorkflow">
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
        <step id = "start">
            <action>helloWorld</action>
            <app>HelloWorld</app>
            <device>hwTest</device>
            <input></input>
            <next next="1">
                <flag action="regMatch">
                    <args>
                        <regex format="regex">(.*)</regex>
                    </args>
                    <filters>
                    </filters>

                </flag>
            </next>
            <error next="1"></error>
        </step>
        <step id = "1">
            <action>repeatBackToMe</action>
            <app>HelloWorld</app>
            <device>hwTest</device>
            <input>
                <call format="string">Hello World</call>
            </input>
            <next>
            </next>
            <error next="1"></error>
        </step>
    </steps>
</workflow>
