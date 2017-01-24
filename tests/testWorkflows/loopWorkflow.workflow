<?xml version="1.0"?>
<workflow name="loopWorkflow">
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
            <action>returnPlusOne</action>
            <app>HelloWorld</app>
            <device>hwTest</device>
            <input>
                <number format="str">
                    {%- if steps | length > 0 -%}
                        {%- set x = steps | outputFrom(-1) -%}
                    {%- endif -%}

                    {%- if x is not none and x is defined -%}
                        {{x}}
                    {%- else -%}
                        1
                    {%- endif -%}
                </number>
            </input>
            <next step="start">
                <flag action="regMatch">
                    <args>
                        <regex format="str">1|2|3|4</regex>
                    </args>
                    <filters>
                    </filters>
                </flag>
            </next>
            <next step="1">
                <flag action="regMatch">
                    <args>
                        <regex format="str">5</regex>
                    </args>
                    <filters>
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
                <call format="str">{{steps | outputFrom(-1)}}</call>
            </input>
            <error step="1"></error>
        </step>
    </steps>
</workflow>
