<template>
	<div class="space-y-4">
		<!-- Show this block if siteVersion is "Version 14" -->
		<div v-if="siteVersion === 'Version 14'">
			<AlertBanner
				title="Great!! You do not seem to have any slow queries"
				type="info"
				v-if="show"
			/>
			<div>
				<ObjectList :options="slowQueriesData" />
			</div>
		</div>

		<!-- Show this alert banner for other versions (specifically Version 15) -->
		<div v-else>
			<AlertBanner
				title="Performance Tuning coming soon for Version 15"
				type="info"
			/>
		</div>
	</div>
</template>

<script>
import { defineAsyncComponent, h } from 'vue';
import { ListView, FormControl, Dialog } from 'frappe-ui';
import ObjectList from '../../../src2/components/ObjectList.vue';
import AlertBanner from '../../../src2/components/AlertBanner.vue';
import { renderDialog } from '../../utils/components';

export default {
	name: 'SitePerformance',
	props: ['siteName', 'siteVersion'],
	components: {
		ListView,
		FormControl,
		Dialog,
		ObjectList,
		AlertBanner
	},
	data() {
		return {
			show: null
		};
	},
	computed: {
		slowQueriesData() {
			return {
				experimental: true,
				documentation: 'https://optibizpro.com/docs/performance-tuning',
				data: () => this.$resources.slowQueries.data.data,
				onRowClick: row => {
					const SlowQueryDialog = defineAsyncComponent(() =>
						import('./SiteMariaDBSlowQueryDialog.vue')
					);
					renderDialog(
						h(SlowQueryDialog, {
							siteName: this.siteName,
							query: row.query,
							duration: row.duration,
							count: row.count,
							rows_examined: row.rows_examined,
							rows_sent: row.rows_sent,
							example: row.example
						})
					);
				},
				columns: [
					{
						label: 'Query',
						fieldname: 'query',
						class: 'font-mono',
						width: '500px'
					},
					{
						label: 'Duration',
						fieldname: 'duration',
						class: 'text-gray-600',
						width: 0.5
					},
					{
						label: 'Rows Examined',
						fieldname: 'rows_examined',
						class: 'text-gray-600',
						width: 0.5
					},
					{
						label: 'Rows Sent',
						fieldname: 'rows_sent',
						class: 'text-gray-600',
						width: 0.5
					},
					{
						label: 'Count',
						fieldname: 'count',
						class: 'text-gray-600',
						width: 0.5
					}
				]
			};
		}
	},
	methods: {
		getDateTimeRange() {
			const now = new Date();
			const startDateTime = new Date(now.getTime() - 24 * 60 * 60 * 1000);
			const formatDateTime = date => {
				const year = date.getFullYear();
				const month = String(date.getMonth() + 1).padStart(2, '0');
				const day = String(date.getDate()).padStart(2, '0');
				const hours = String(date.getHours()).padStart(2, '0');
				const minutes = String(date.getMinutes()).padStart(2, '0');
				const seconds = String(date.getSeconds()).padStart(2, '0');
				return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
			};

			const endDateTime = formatDateTime(now);
			const startDateTimeFormatted = formatDateTime(startDateTime);

			return {
				startDateTime: startDateTimeFormatted,
				endDateTime: endDateTime
			};
		}
	},
	resources: {
		slowQueries() {
			const { startDateTime, endDateTime } = this.getDateTimeRange();
			return {
				url: 'press.api.analytics.mariadb_slow_queries',
				params: {
					name: this.siteName,
					start_datetime: startDateTime,
					stop_datetime: endDateTime,
					max_lines: 10,
					search_pattern: '.*',
					normalize_queries: true,
					analyze: false
				},
				onSuccess(data) {
					if (!data.data) {
						this.show = true;
					}
				},
				auto: true,
				initialData: { columns: [], data: [] }
			};
		}
	}
};
</script>
