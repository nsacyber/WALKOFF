<?xml version="1.0"?>
<workflow name="dataflowWorkflow">
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
            <action>Add Three</action>
            <app>HelloWorld</app>
            <device>hwTest</device>
            <inputs>
                <num1>1</num1>
                <num2>2</num2>
                <num3>3</num3>
            </inputs>
            <next step="1"/>
        </step>
        <step id="1">
            <action>Add To Previous</action>
            <app>HelloWorld</app>
            <device>hwTest</device>
            <inputs>
                <num>4</num>
            </inputs>
        </step>
    </steps>
</workflow>
