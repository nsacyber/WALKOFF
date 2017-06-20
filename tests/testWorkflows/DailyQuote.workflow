<?xml version="1.0"?>
<workflow name="DailyQuoteWorkflow">
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
            <action>getQuote</action>
            <app>DailyQuote</app>
            <device>hwTest</device>
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
    </steps>
</workflow>
