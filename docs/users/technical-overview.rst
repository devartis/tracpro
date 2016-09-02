Technical Overview
===================

Concepts
--------------------

* `Polls` are RapidPro flows. Click on the name of a poll to see a summary of the responses over time and dates it was conducted.
* `PollRuns` are the dates a poll was conducted. Click on a poll date to see a summary of just the responses for that date, participation among reporter groups, send a message to contacts, individual responses, and export responses.
* `Contacts` are the same as in RapidPro, they are the respondents of polls.
* `Supervisors` could be, for example, a provincial monitoring officer in a ministry. They are meant to see a particular region or multiple regions, and encourage participation by seeing who is responding, and restart polls. Supervisors also manage contacts.
* `Administrators` setup TracPro for an org and can manage everything supervisors can, in addition to managing supervisors.
* `Regions` are administrative areas, and can be anything, for example a city, county, or state in the USA. They must be configured as contact groups in RapidPro first. Regions can be made hierarchical in TracPro. For example, a supervisor who has access only to Kampala, would not have access to all of Africa's regional data, and a second supervisor who had access to Africa, would have access to data for all sub-regions within Africa.
* `Reporter groups` are types of contacts, such as head teachers, or grade 5 teachers. They must be configured as contact groups in RapidPro first.
* `Recent Indicators` allow users to compare baseline poll results to follow up poll results over time. For instance, if a poll was sent out to gather enrollment numbers at the start of the term, that could be selected as the baseline poll, and a follow up poll could be the poll sent out over the term asking for attendance numbers. Users may also spoof poll data to create sample results to chart on Recent Indicators.
* `Inbox Messages` allow users to view and send unsolicited messages, that is, messages outside of a flow, to contacts.
* `Trackers` allow users to alter contact group membership based on contact field values through group rules.
* `Group Rules` are rules that users can add to add or remove contacts from arbitrary groups based on the configured thresholds in the related tracker.
* `Alerts` are triggered based on changes to group membership. Users can choose a flow that will be executed when configured group membership change events.

Features
--------------------

**Administrator accounts**: Configure a dashboard for any org, such as choosing polls, reporter groups, and regions to make available.

**Supervisor management**: Administrators can easily add, remove, and configure supervisors. Administators set up any desired access to particular regions for supervisors. Supervisors have access to data for their regions and to Homepage Poll data, Contacts, Inbox Messages and Recent Indicators.

**Contact management**: Supervisors can create, manage, and remove contacts, including changing their region, reporter group, facility and language, and all those changes are synchronized in the background with RapidPro.

**Start polls**: Supervisors can start any poll brought into TracPro from the Homepage.

**Send messages**: Send messages about polls to non-responsive contacts, responsive contacts or all contacts of a group. Select a Poll, select a date that the poll ran from the list of dates it was conducted on (PollRuns), choose the Participation tab, and click the button to "Send Message..." and choose whether to send it to respondents or non-respondents. These messages can be viewed from the Message Log.

**Activity**: See the most active regions and the most active reporter groups.

**Participation**: See participation of every contact in all polls on one page.

**Right-to-left (RTL) language support**: Any language can be displayed, whether left-to-right or right-to-left with content switching correctly too.

**Easy translations**: TracPro uses Transifex.com, the easy way to add a translation. Anyone can add translations that are then available for others to use in their TracPro dashboard.

**Automatic charts**: Simple analytics are automatically created because TracPro and RapidPro know what the type of response is for a flow step, i.e. numeric, multiple choice, open-ended text, or audio recording from IVR. Responses can be seen for time-series or for one poll issue.

**Export as CSV**: Export data from TracPro into CSV format, which can easily be imported into Microsoft Excel or other tools.

**Edit poll names**: Change any poll description.

**Mobile-ready**: TracPro works in smartphone and tablet browsers.