<?xml version="1.0" ?>
<workflows>
	<workflow name="cyberAnalyticWorkflow">
		<options>
			<enabled>true</enabled>
			<scheduler autorun="false" type="cron">
				<hours>*</hours>
				<minutes>*/0.1</minutes>
				<day>*</day>
				<month>11-12</month>
			</scheduler>
		</options>
		<start>start</start>
		<steps>
			<step id="start">
				<id>start</id>
				<app>CyberAnalytic</app>
				<action>begin_monitoring</action>
				<device/>
				<input/>
			</step>
		</steps>
	</workflow>
</workflows>
