<?xml version="1.0" ?>
<workflows>
	<workflow name="helloWorldWorkflow">
		<options>
			<enabled>true</enabled>
			<scheduler autorun="false" type="cron">
				<hours>*</hours>
				<minutes>*/0.1</minutes>
				<day>*</day>
				<month>11-12</month>
			</scheduler>
		</options>
		<steps>
			<step id="start">
				<id>start</id>
				<app>HelloWorld</app>
				<action>repeatBackToMe</action>
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
								<args/>
							</filter>
						</filters>
					</flag>
				</next>
				<error step="1"/>
			</step>
		</steps>
	</workflow>
</workflows>
