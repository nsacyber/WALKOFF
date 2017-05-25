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
				<id>1</id>
				<app>Lifx</app>
				<action>breathe_effect</action>
				<device>LIFX 12cf1f</device>
				<position>
					<x>494.055032258</x>
					<y>437.567112283</y>
				</position>
				<input>
					<power_on format="str">true</power_on>
					<color format="str">red</color>
					<period format="int">1</period>
					<peak format="int">5</peak>
					<persist format="str">true</persist>
					<from_color format="str">blue</from_color>
					<cycles format="int">10</cycles>
				</input>
				<next step="2"/>
			</step>
			<step id="2">
				<id>2</id>
				<app>Lifx</app>
				<action>toggle_power</action>
				<device>LIFX 12cf1f</device>
				<position>
					<x>452.952347395</x>
					<y>381.806710298</y>
				</position>
				<input>
					<duration format="int">2</duration>
				</input>
			</step>
		</steps>
	</workflow>
</workflows>
