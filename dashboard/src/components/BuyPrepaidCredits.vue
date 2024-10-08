<template>
	<div>
		<FormControl
			v-if="step == 'Get Amount'"
			class="mb-2"
			label="Credits"
			v-model.number="creditsToBuy"
			name="amount"
			autocomplete="off"
			type="number"
			:min="minimumAmount"
		/>
		<label
			class="block"
			:class="{
				'h-0.5 opacity-0': step != 'Add Card Details',
				'mt-4': step == 'Add Card Details'
			}"
		>
			<span class="text-sm leading-4 text-gray-700">
				Credit or Debit Card
			</span>
			<div
				class="form-input mt-2 block w-full py-2 pl-3"
				ref="card-element"
			></div>
			<ErrorMessage class="mt-1" :message="cardErrorMessage" />
		</label>

		<FormControl
			v-if="step == 'Get Amount'"
			label="Total Amount + GST(if applicable)"
			disabled
			v-model="total"
			name="total"
			autocomplete="off"
			type="number"
		/>

		<div v-if="step == 'Setting up Stripe'" class="mt-8 flex justify-center">
			<Spinner class="h-4 w-4 text-gray-600" />
		</div>
		<ErrorMessage
			class="mt-2"
			:message="$resources.createPaymentIntent.error || errorMessage"
		/>
		<div class="mt-4 flex w-full justify-between">
			<MidtransLogo />
			<div v-if="step == 'Get Amount'">
				<Button
					variant="solid"
					@click="$resources.createPaymentIntent.submit()"
					:loading="$resources.createPaymentIntent.loading"
				>
					Next
				</Button>
			</div>
			<div v-if="step == 'Add Card Details'">
				<Button @click="$emit('cancel')"> Cancel </Button>
				<Button
					class="ml-2"
					variant="solid"
					@click="onBuyClick"
					:loading="paymentInProgress"
				>
					Buy Credits
				</Button>
			</div>
		</div>
	</div>
</template>
<script>
import StripeLogo from '@/components/StripeLogo.vue';
import { loadStripe } from '@stripe/stripe-js';
import MidtransLogo from './MidtransLogo.vue';

export default {
	name: 'BuyPrepaidCredits',
	components: {
		StripeLogo,
		MidtransLogo
	},
	props: {
		minimumAmount: {
			default: 0
		}
	},
	mounted() {
		this.updateTotal();
	},
	watch: {
		creditsToBuy() {
			this.updateTotal();
		}
	},
	data() {
		return {
			step: 'Get Amount', // Get Amount / Add Card Details
			clientSecret: null,
			creditsToBuy: this.minimumAmount || null,
			total: this.minimumAmount,
			cardErrorMessage: null,
			errorMessage: null,
			paymentInProgress: false
		};
	},
	resources: {
		createPaymentIntent() {
			return {
				url: 'press.api.billing.create_payment_intent_for_buying_credits',
				params: {
					amount: this.creditsToBuy
				},
				validate() {
					if (
						this.creditsToBuy < this.minimumAmount &&
						!this.$account.team.erpnext_partner
					) {
						return `Amount must be greater than ${this.minimumAmount}`;
					}
				},
				async onSuccess(data) {
					this.step = 'Setting up Stripe';
					let { publishable_key, client_secret } = data;
					this.clientSecret = client_secret;
					this.stripe = await loadStripe(publishable_key);
					this.elements = this.stripe.elements();
					let theme = this.$theme;
					let style = {
						base: {
							color: theme.colors.black,
							fontFamily: theme.fontFamily.sans.join(', '),
							fontSmoothing: 'antialiased',
							fontSize: '13px',
							'::placeholder': {
								color: theme.colors.gray['400']
							}
						},
						invalid: {
							color: theme.colors.red['600'],
							iconColor: theme.colors.red['600']
						}
					};
					this.card = this.elements.create('card', {
						hidePostalCode: true,
						style: style,
						classes: {
							complete: '',
							focus: 'bg-gray-100'
						}
					});

					this.step = 'Add Card Details';
					this.$nextTick(() => {
						this.card.mount(this.$refs['card-element']);
					});

					this.card.addEventListener('change', event => {
						this.cardErrorMessage = event.error?.message || null;
					});
					this.card.addEventListener('ready', () => {
						this.ready = true;
					});
				}
			};
		}
	},
	methods: {
		updateTotal() {
			if (this.$account.team.currency === 'INR') {
				this.total = Number(
					(
						this.creditsToBuy +
						this.creditsToBuy * this.$account.billing_info.gst_percentage
					).toFixed(2)
				);
			} else {
				this.total = this.creditsToBuy;
			}
		},
		setupStripe() {
			this.$resources.createPaymentIntent.submit();
		},
		async onBuyClick() {
			this.paymentInProgress = true;
			let payload = await this.stripe.confirmCardPayment(this.clientSecret, {
				payment_method: {
					card: this.card
				}
			});

			this.paymentInProgress = false;
			if (payload.error) {
				this.errorMessage = payload.error.message;
			} else {
				this.$emit('success');
				this.errorMessage = null;
				this.creditsToBuy = null;
			}
		}
	}
};
</script>
