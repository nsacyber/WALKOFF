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
		<start>start</start>
		<steps>
			<step id="1">
				<id>1</id>
				<app>DailyQuote</app>
				<action>quoteIntro</action>
				<device/>
				<position>
					<x>-90</x>
					<y>-90</y>
				</position>
				<input/>
				<next step="2"/>
			</step>
			<step id="start">
				<id>start</id>
				<app>HelloWorld</app>
				<action>repeatBackToMe</action>
				<device>hwTest</device>
				<position>
					<x>-90</x>
					<y>-10</y>
				</position>
				<input>
					<call format="str">Hello World</call>
				</input>
				<error step="1"/>
			</step>
			<step id="3">
				<id>3</id>
				<app>DailyQuote</app>
				<action>forismaticQuote</action>
				<device/>
				<position>
					<x>30</x>
					<y>-90</y>
				</position>
				<input>
					<url format="str">None</url>
				</input>
			</step>
			<step id="2">
				<id>2</id>
				<app>DailyQuote</app>
				<action>getQuote</action>
				<device/>
				<position>
					<x>-90</x>
					<y>-170</y>
				</position>
				<input/>
			</step>
		</steps>
	</workflow>
	<workflow name="test2">
		<options>
			<enabled>true</enabled>
			<scheduler autorun="false" type="cron">
				<sDT>2016-1-1 12:00:00</sDT>
				<interval>0.1</interval>
				<eDT>2016-3-15 12:00:00</eDT>
			</scheduler>
		</options>
		<start>90e56daa-9c52-aefe-90e5-3a88f6c301d7</start>
		<steps>
			<step id="1">
				<id>1</id>
				<app>Lifx</app>
				<action>breathe_effect</action>
				<risk>0</risk>
				<device/>
				<position>
					<x>490</x>
					<y>350</y>
				</position>
				<input>
					<power_on format="str">None</power_on>
					<color format="str">None</color>
					<period format="int">0</period>
					<peak format="int">0</peak>
					<persist format="str">None</persist>
					<from_color format="str">None</from_color>
					<cycles format="int">0</cycles>
				</input>
				<next step="2"/>
			</step>
			<step id="08d80757-7ed0-ddcf-0cfb-e2859dfa63d5">
				<id>08d80757-7ed0-ddcf-0cfb-e2859dfa63d5</id>
				<app>Lifx</app>
				<action>pulse_effect</action>
				<risk>0</risk>
				<device/>
				<position>
					<x>590</x>
					<y>190</y>
				</position>
				<input>
					<power_on format="str">None</power_on>
					<color format="str">None</color>
					<period format="int">0</period>
					<persist format="str">None</persist>
					<from_color format="str">None</from_color>
					<cycles format="int">0</cycles>
				</input>
			</step>
			<step id="3">
				<id>3</id>
				<app>Lifx</app>
				<action>set_state</action>
				<risk>0</risk>
				<device/>
				<position>
					<x>490</x>
					<y>190</y>
				</position>
				<input>
					<color format="str">None</color>
					<duration format="int">0</duration>
					<brightness format="int">0</brightness>
					<power format="str">None</power>
					<infrared format="int">0</infrared>
				</input>
			</step>
			<step id="2">
				<id>2</id>
				<app>Lifx</app>
				<action>pulse_effect</action>
				<risk>0</risk>
				<device/>
				<position>
					<x>490</x>
					<y>270</y>
				</position>
				<input>
					<power_on format="str">None</power_on>
					<color format="str">None</color>
					<period format="int">0</period>
					<persist format="str">None</persist>
					<from_color format="str">None</from_color>
					<cycles format="int">0</cycles>
				</input>
				<next step="3"/>
			</step>
			<step id="90e56daa-9c52-aefe-90e5-3a88f6c301d7">
				<id>90e56daa-9c52-aefe-90e5-3a88f6c301d7</id>
				<app>Lifx</app>
				<action>breathe_effect</action>
				<risk>0</risk>
				<device/>
				<position>
					<x>590</x>
					<y>350</y>
				</position>
				<input>
					<power_on format="str">None</power_on>
					<color format="str">None</color>
					<period format="int">0</period>
					<peak format="int">0</peak>
					<persist format="str">None</persist>
					<from_color format="str">None</from_color>
					<cycles format="int">0</cycles>
				</input>
				<next step="08d80757-7ed0-ddcf-0cfb-e2859dfa63d5"/>
			</step>
		</steps>
	</workflow>
	<workflow name="testWorkflow">
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
				<app>HelloWorld</app>
				<action>helloWorld</action>
				<position>
					<x>390</x>
					<y>330</y>
				</position>
				<input/>
				<next step="2"/>
			</step>
			<step id="2">
				<id>2</id>
				<app>HelloWorld</app>
				<action>repeatBackToMe</action>
				<position>
					<x>390</x>
					<y>250</y>
				</position>
				<input>
					<call format="str">None</call>
				</input>
			</step>
		</steps>
	</workflow>
</workflows>
