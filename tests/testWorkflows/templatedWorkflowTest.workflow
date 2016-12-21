<?xml version="1.0"?>
<workflow name="templatedWorkflow">
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
        <step>
            <id>start</id>
            <action>helloWorld</action>
            <app>HelloWorld</app>
            <device>hwTest</device>
            <input>
            </input>
            <next next="1">
                <flag action="regMatch">
                    <args>
                        <regex format="regex">(.*)</regex>
                    </args>
                    <filters>
                        <filter action="length">
                            <args></args>
                        </filter>
                    </filters>
                </flag>
            </next>
            <error next="1"></error>
        </step>
        <step>
            <id>1</id>
            <action>repeatBackToMe</action>
            <app>HelloWorld</app>
            <device>hwTest</device>
            <input>
                <call format="string">{{steps | out("start")}}</call>
            </input>
            <next>
            </next>
            <error next="1"></error>
        </step>
    </steps>
</workflow>
