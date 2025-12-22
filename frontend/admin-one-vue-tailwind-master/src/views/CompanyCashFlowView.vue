<script setup>
import { onBeforeMount, computed, ref, watch, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { mdiTableBorder, mdiArrowDownBoldCircle, mdiCashFast, mdiCreditCard, mdiCalendarClock, mdiCheckDecagram } from '@mdi/js'
import { useMainStore } from '@/stores/main'
import SectionMain from '@/components/SectionMain.vue'
import axios from 'axios'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import BaseButton from '@/components/BaseButton.vue'
import CardBox from '@/components/CardBox.vue'
import FormField from '@/components/FormField.vue'
import FormControl from '@/components/FormControl.vue'
import NotificationBar from '@/components/NotificationBar.vue'
import * as barChartConfig from '@/components/Charts/barChart.config.js'
import BarChart from '@/components/Charts/BarChart.vue'

// Acessa o store principal
const mainStore = useMainStore()
const chartData = ref(null)
const cashflow = computed(() => mainStore.cashFlow)
const router = useRouter()

// --- PAYMENT CONTROLS STATE (NOVO) ---
const statusMessage = ref('')
const statusColor = ref('info')

const cardForm = reactive({
  number: '',
  holder: '',
  expiry: '',
  cvc: ''
})

const scheduleForm = reactive({
  frequency: 'Manual'
})

const setStatus = (msg, color = 'info') => {
  statusMessage.value = msg
  statusColor.value = color
  setTimeout(() => { statusMessage.value = '' }, 5000)
}

// 1. Submit Card (Tokenization)
const submitCard = async () => {
  try {
    await axios.post('http://localhost:5000/company/add-card', {
      token: localStorage.getItem('token'),
      card_number: cardForm.number,
      card_holder_name: cardForm.holder,
      expiry_date: cardForm.expiry
    })
    setStatus("Cartão associado com sucesso!", "success")
    cardForm.number = '' // Clear sensitive data
    cardForm.cvc = ''
  } catch (err) {
    setStatus("Erro ao associar cartão: " + (err.response?.data?.error || err.message), "danger")
  }
}

// 2. Submit Schedule
const submitSchedule = async () => {
  try {
    await axios.post('http://localhost:5000/company/schedule-pay', {
      token: localStorage.getItem('token'),
      frequency_type: scheduleForm.frequency
    })
    setStatus("Agendamento atualizado!", "success")
  } catch (err) {
    setStatus("Erro ao agendar: " + (err.response?.data?.error || err.message), "danger")
  }
}

// 3. Process Payment (Manual Trigger)
const processPayment = async () => {
  if (!confirm("Tem a certeza? Vai processar pagamentos reais para todos os funcionários.")) return

  try {
    // Simulação da Assinatura Digital do Admin (Client-side)
    const mockSignature = "sig_rsa_sha256_" + Date.now().toString(16)

    const response = await axios.post('http://localhost:5000/company/pay', {
      token: localStorage.getItem('token')
    }, {
      headers: { 'X-Admin-Signature': mockSignature }
    })

    if (response.data.total_paid > 0) {
        setStatus(`Sucesso! Total Pago: €${response.data.total_paid} a ${response.data.recipients_count} funcionários.`, "success")
        // Refresh cashflow data
        mainStore.getCompanyCashFlow()
    } else {
        setStatus("Processado, mas não havia pagamentos pendentes.", "warning")
    }
  } catch (err) {
    setStatus("Falha no pagamento: " + (err.response?.data?.error || err.message), "danger")
  }
}

const invoice = (filename) => {
  filename = 'invoice.pdf'
  axios({
    url: `http://localhost:5000/invoice?filename=${filename}`,
    method: 'GET',
    responseType: 'blob',
  })
  .then((response) => {
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  })
  .catch((error) => {
    alert(error.message);
  });
}

onBeforeMount(() => {
  mainStore.getCompanyCashFlow()
})

watch(cashflow, (newCashflow) => {
  if (newCashflow && newCashflow.status === 'Ok') {
    const apiDataJuly = {
      profit: newCashflow.July.profit,
      totalEmployeesPayment: newCashflow.July.totalEmployeesPayment,
      vat_value: newCashflow.July.vat_value,
      prodCosts: newCashflow.July.prod_costs
    }
    const apiDataAugust = {
      profit: newCashflow.August.profit,
      totalEmployeesPayment: newCashflow.August.totalEmployeesPayment,
      vat_value: newCashflow.August.vat_value,
      prodCosts: newCashflow.August.prod_costs
    }
    const apiDataSeptember = {
      profit: newCashflow.September.profit,
      totalEmployeesPayment: newCashflow.September.totalEmployeesPayment,
      vat_value: newCashflow.September.vat_value,
      prodCosts: newCashflow.August.prod_costs
    }

    const dataForThreeMonths = [
      apiDataJuly.profit,
      apiDataAugust.profit,
      apiDataSeptember.profit
    ]

    const employeePaymentsForThreeMonths = [
      apiDataJuly.totalEmployeesPayment,
      apiDataAugust.totalEmployeesPayment,
      apiDataSeptember.totalEmployeesPayment
    ]

    const vatForThreeMonths = [
      parseInt(apiDataJuly.vat_value),
      parseInt(apiDataAugust.vat_value),
      parseInt(apiDataSeptember.vat_value)
    ]

    const subscription = [ 500, 500, 500 ]

    const prodCosts = [
      apiDataJuly.prodCosts,
      apiDataAugust.prodCosts,
      apiDataSeptember.prodCosts
    ]

    chartData.value = barChartConfig.generateBarChartData({
      labels: ['July', 'August', 'September'],
      datasets: [
        {
          label: 'Profit',
          data: dataForThreeMonths,
          backgroundColor: 'rgba(75, 192, 192, 0.2)',
          borderColor: 'rgba(75, 192, 192, 1)',
          borderWidth: 1
        },
        {
          label: 'Employee Payments',
          data: employeePaymentsForThreeMonths,
          backgroundColor: 'rgba(153, 102, 255, 0.2)',
          borderColor: 'rgba(153, 102, 255, 1)',
          borderWidth: 1
        },
        {
          label: 'VAT value',
          data: vatForThreeMonths,
          backgroundColor: 'rgba(255, 159, 64, 0.2)',
          borderColor: 'rgba(255, 159, 64, 1)',
          borderWidth: 1
        },
        {
          label: 'Subscription',
          data: subscription,
          backgroundColor: 'rgba(255, 159, 64, 0.2)',
          borderColor: 'rgba(255, 159, 64, 1)',
          borderWidth: 1
        },
        {
          label: 'Production costs',
          data: prodCosts,
          backgroundColor: 'rgba(255, 159, 64, 0.2)',
          borderColor: 'rgba(255, 159, 64, 1)',
          borderWidth: 1
        }
      ]
    })
  }
}, { immediate: true })

</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton :icon="mdiCashFast" title="Automatic Payments Control" main>
        <BaseButton
          target="_blank"
          :icon="mdiArrowDownBoldCircle"
          label="Invoices"
          color="info"
          rounded-full
          small
          @click="invoice"
        />
      </SectionTitleLineWithButton>

      <NotificationBar v-if="statusMessage" :color="statusColor" :icon="mdiCheckDecagram">
        {{ statusMessage }}
      </NotificationBar>

      <div class="grid grid-cols-1 gap-6 lg:grid-cols-2 mb-6">

        <CardBox title="Process Payroll" :icon="mdiCashFast" class="h-full">
          <p class="mb-4 text-gray-600">
            Calculate pending commissions based on sales and process payments via FastPay.
          </p>
          <div class="flex justify-center mt-6">
            <BaseButton
              color="danger"
              label="Pay Commissions Now"
              :icon="mdiCashFast"
              @click="processPayment"
              large
            />
          </div>
        </CardBox>

        <CardBox title="Schedule" :icon="mdiCalendarClock" class="h-full" is-form @submit.prevent="submitSchedule">
          <FormField label="Payment Frequency">
            <FormControl v-model="scheduleForm.frequency" :options="['Manual', 'Weekly', 'Monthly']" />
          </FormField>
          <BaseButton type="submit" color="info" label="Save Schedule" outline />
        </CardBox>

      </div>

      <CardBox title="Company Payment Method" :icon="mdiCreditCard" is-form @submit.prevent="submitCard" class="mb-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FormField label="Card Holder">
            <FormControl v-model="cardForm.holder" placeholder="Company Name" required />
          </FormField>
          <FormField label="Card Number">
            <FormControl v-model="cardForm.number" placeholder="0000 0000 0000 0000" required />
          </FormField>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormField label="Expiry Date">
                <FormControl v-model="cardForm.expiry" placeholder="MM/YY" required />
            </FormField>
            <FormField label="CVC">
                <FormControl v-model="cardForm.cvc" placeholder="123" type="password" required />
            </FormField>
        </div>
        <template #footer>
            <BaseButton type="submit" color="success" label="Link Card (Secure Token)" />
        </template>
      </CardBox>

      <SectionTitleLineWithButton :icon="mdiTableBorder" title="Cash Flow Analytics" />

      <div class="grid grid-cols-1 gap-6 mb-6">
        <CardBox>
          <div class="p-6">
            <h3 class="text-lg font-semibold">Current Balance</h3>
            <p class="text-2xl font-bold text-green-600">+{{ cashflow.profit || 0 | currency }} $</p>
          </div>
        </CardBox>
      </div>

      <div class="grid grid-cols-1 gap-6">
        <CardBox class="mb-6">
          <div v-if="chartData">
            <BarChart :data="chartData" class="h-96" />
          </div>
        </CardBox>
      </div>

      <div class="mt-6">
        <h3 class="text-lg font-semibold mb-4">July</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <CardBox v-for="(employee, index) in cashflow.July?.employees || []" :key="index">
            <div class="p-6">
              <h4 class="font-bold">{{ employee.Username }}</h4>
              <p>Total Sales: {{ employee.TotalSales }}</p>
              <p>Total Commission: {{ employee.TotalCommission }}</p>
              <p>Commission Percentage: {{ employee.CommissionPercentage }}%</p>
            </div>
          </CardBox>
        </div>
      </div>

      <div class="mt-6">
        <h3 class="text-lg font-semibold mb-4">August</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <CardBox v-for="(employee, index) in cashflow.August?.employees || []" :key="index">
            <div class="p-6">
              <h4 class="font-bold">{{ employee.Username }}</h4>
              <p>Total Sales: {{ employee.TotalSales }}</p>
              <p>Total Commission: {{ employee.TotalCommission }}</p>
              <p>Commission Percentage: {{ employee.CommissionPercentage }}%</p>
            </div>
          </CardBox>
        </div>
      </div>

      <div class="mt-6">
        <h3 class="text-lg font-semibold mb-4">September</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <CardBox v-for="(employee, index) in cashflow.September?.employees || []" :key="index">
            <div class="p-6">
              <h4 class="font-bold">{{ employee.Username }}</h4>
              <p>Total Sales: {{ employee.TotalSales }}</p>
              <p>Total Commission: {{ employee.TotalCommission }}</p>
              <p>Commission Percentage: {{ employee.CommissionPercentage }}%</p>
            </div>
          </CardBox>
        </div>
      </div>
    </SectionMain>
  </LayoutAuthenticated>
</template>
