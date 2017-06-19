<?xml version="1.0" ?>
<workflows>
	<workflow name="Test">
		<options>
			<enabled>true</enabled>
			<scheduler autorun="false" type="cron">
				<sDT>2016-1-1 12:00:00</sDT>
				<interval>0.1</interval>
				<eDT>2016-3-15 12:00:00</eDT>
			</scheduler>
		</options>
		<start>1</start>
		<steps>
			<step id="1">
				<name>1</name>
				<app>Lifx</app>
				<action>breathe</action>
				<device>Light2</device>
				<position>
					<x>490</x>
					<y>430</y>
				</position>
				<inputs>
					<power_on>True</power_on>
					<color>red</color>
					<period>1.0</period>
					<peak>0.5</peak>
					<persist>False</persist>
					<from_color>blue</from_color>
					<cycles>5.0</cycles>
					<wait>False</wait>
				</inputs>
				<next step="3"/>
			</step>
			<step id="3">
				<name>3</name>
				<app>Lifx</app>
				<action>pulse</action>
				<device>Light1</device>
				<position>
					<x>410</x>
					<y>330</y>
				</position>
				<inputs>
					<power_on>True</power_on>
					<color>red</color>
					<period>1.0</period>
					<persist>True</persist>
					<from_color>blue</from_color>
					<cycles>10.0</cycles>
					<wait>False</wait>
				</inputs>
				<next step="2"/>
			</step>
			<step id="2">
				<name>3</name>
				<app>Utilities</app>
				<action>select json</action>
				<position>
					<x>410</x>
					<y>330</y>
				</position>
				<inputs>
					<json>@3</json>
					<path>
					    <item>results</item>
					</path>
				</inputs>
			</step>
		</steps>
	</workflow>
</workflows>
