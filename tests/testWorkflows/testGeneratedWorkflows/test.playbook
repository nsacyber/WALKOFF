<?xml version="1.0" ?>
<workflows>
	<workflow name="helloWorldWorkflow">
		
    
		<options>
			
        
			<enabled>true</enabled>
			
        
			<scheduler autorun="false" type="cron">
				
            
				<month>11-12</month>
				
            
				<day>*</day>
				
            
				<hours>*</hours>
				
            
				<minutes>*/0.1</minutes>
				
        
			</scheduler>
		</options>
		<steps>
			<step id="start">
				<id>start</id>
				<app>HelloWorld</app>
				<action>repeatBackToMe</action>
				<device>hwTest</device>
				<inputs>
					<call>Hello World</call>
				</inputs>
				<next step="1">
					<flag action="regMatch">
						<args>
							<regex>(.*)</regex>
						</args>
						<filters>
							<filter action="length"/>
						</filters>
					</flag>
				</next>
				<error step="1"/>
			</step>
		</steps>
	</workflow>
</workflows>
