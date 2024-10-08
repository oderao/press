<template>
	<WizardCard v-if="options">
		<div class="mb-6 text-center">
			<h1 class="text-2xl font-bold">Create a new Self Hosted Server</h1>
		</div>
		<Steps :steps="steps">
			<template
				v-slot="{ active: activeStep, next, previous, hasPrevious, hasNext }"
			>
				<div class="mt-8"></div>
				<SelfHostedHostname
					v-show="activeStep.name === 'SelfHostedHostname'"
					v-model:title="title"
				/>
				<div class="mt-4">
					<SelfHostedServerPlan
						v-model:selectedPlan="selectedPlan"
						:options="options"
						v-show="activeStep.name === 'SelfHostedServerPlan'"
					/>
				</div>
				<div>
					<SelfHostedServerForm
						v-show="activeStep.name === 'ServerDetails'"
						v-model:appPublicIP="appPublicIP"
						v-model:appPrivateIP="appPrivateIP"
						v-model:dbPublicIP="dbPublicIP"
						v-model:dbPrivateIP="dbPrivateIP"
						v-model:error="ipInvalid"
					/>
				</div>

				<div class="mt-4" v-if="activeStep.name === 'VerifyServer'">
					<SelfHostedServerVerify v-model:ssh_key="ssh_key" />

					<Button
						v-if="$resources.verify.data === null"
						@click="$resources.verify.submit()"
						:loading="$resources.verify.loading"
						variant="solid"
					>
						Verify Server
					</Button>
					<Button
						v-else
						:icon-left="playOutput ? 'check' : 'x'"
						variant="solid"
						:theme="playOutput ? 'gray' : 'red'"
						:appearance="playOutput ? 'success' : 'warning'"
						@click="$resources.verify.submit()"
					>
						{{ playOutput ? 'Server Verified' : 'Server Unreachable' }}
					</Button>
				</div>
				<ErrorMessage class="mt-2" :message="$resources.verify.error" />
				<div class="mt-4">
					<!-- Region consent checkbox -->
					<div class="my-6" v-if="!hasNext">
						<FormControl
							id="region-consent"
							type="checkbox"
							label="I agree that the laws of the region selected by me shall stand
							applicable to me and Optibizpro."
							class="rounded border-gray-300 focus:ring-blue-500"
							v-model="agreedToRegionConsent"
						/>
					</div>
					<ErrorMessage class="mb-4" :message="$resources.newServer.error" />

					<div class="flex justify-between">
						<Button v-if="hasPrevious" @click="previous"> Back </Button>

						<Button
							v-if="hasNext"
							class="ml-auto"
							variant="solid"
							@click="nextStep(activeStep, next)"
							:class="{ 'mt-2': hasPrevious }"
						>
							Next
						</Button>
						<Button
							v-show="!hasNext"
							class="ml-auto"
							variant="solid"
							:disabled="!playOutput || !this.agreedToRegionConsent"
							@click="setupServers"
							:loading="$resources.setupServer.loading"
						>
							Setup Server
						</Button>
					</div>
				</div>
			</template>
		</Steps>
	</WizardCard>
</template>

<script>
import WizardCard from '@/components/WizardCard.vue';
import Steps from '@/components/Steps.vue';
import SelfHostedHostname from './NewSelfHostedServerHostname.vue';
import SelfHostedServerForm from './NewSelfHostedServerForm.vue';
import SelfHostedServerVerify from './SelfHostedServerVerify.vue';
import SelfHostedServerPlan from './SelfHostedServerPlan.vue';
export default {
	name: 'NewSelfHostedServer',
	components: {
		WizardCard,
		Steps,
		SelfHostedHostname,
		SelfHostedServerPlan,
		SelfHostedServerForm,
		SelfHostedServerVerify
	},
	data() {
		return {
			title: null,
			options: null,
			appPublicIP: null,
			appPrivateIP: null,
			dbPublicIP: null,
			dbPrivateIP: null,
			validationMessage: null,
			serverDoc: null,
			ssh_key: null,
			selectedPlan: null,
			dnsErrorMessage: null,
			ipInvalid: false,
			unreachable: false,
			playOutput: false,
			agreedToRegionConsent: false,
			steps: [
				{
					name: 'SelfHostedHostname',
					validate: () => {
						return this.title;
					}
				},
				{
					name: 'SelfHostedServerPlan',
					validate: () => {
						return this.selectedPlan;
					}
				},
				{
					name: 'ServerDetails',
					validate: () => {
						return this.appPublicIP;
					}
				},
				{
					name: 'VerifyServer',
					validate: () => {
						return this.playOutput;
					}
				}
			]
		};
	},
	async mounted() {
		const plans = await this.$call('press.api.selfhosted.get_plans');
		this.options = plans.map(plan => {
			plan.disabled = !this.$account.hasBillingInfo;
			plan.vcpu = 'Any';
			return plan;
		});
		this.ssh_key = await this.$call('press.api.selfhosted.sshkey');
	},
	resources: {
		newServer() {
			return {
				url: 'press.api.selfhosted.new',
				params: {
					server: {
						title: this.title,
						app_public_ip: this.appPublicIP,
						app_private_ip: this.appPrivateIP,
						db_public_ip: this.dbPublicIP,
						db_private_ip: this.dbPrivateIP,
						plan: this.selectedPlan
					}
				},
				onSuccess(data) {
					this.serverDoc = data;
				}
			};
		},
		verify() {
			return {
				url: 'press.api.selfhosted.verify',
				params: {
					server: this.serverDoc
				},
				onSuccess(data) {
					this.playOutput = data;
				}
			};
		},
		setupServer() {
			return {
				url: 'press.api.selfhosted.setup',
				params: {
					server: this.serverDoc
				},
				validate() {
					let canCreate = this.title;

					if (!this.agreedToRegionConsent) {
						return 'Please agree to the above consent to create server';
					}
					if (!canCreate) {
						return 'Cannot create server';
					}
				}
			};
		}
	},
	computed: {},
	methods: {
		async nextStep(activeStep, next) {
			if (activeStep.name === 'ServerDetails' && !this.ipInvalid) {
				this.$resources.newServer.submit();
			}
			next();
		},
		async setupServers() {
			await this.$resources.setupServer.submit();
			if (this.agreedToRegionConsent) {
				this.$router.replace(`/servers/`);
			}
		}
	}
};
</script>
