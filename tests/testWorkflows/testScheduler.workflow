<?xml version="1.0" ?>
<workflows>
	<workflow name="helloWorldWorkflow">
		<options>
			<enabled>true</enabled>
			<scheduler autorun="false" type="cron">
				<second>*/4</second>
				<day>*</day>
				<hour>*</hour>
				<month>1-2</month>
			</scheduler>
		</options>
		<start>start</start>
		<steps>
			<step id="start">
				<id>start</id>
				<app>HelloWorld</app>
				<action>repeatBackToMe</action>
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
