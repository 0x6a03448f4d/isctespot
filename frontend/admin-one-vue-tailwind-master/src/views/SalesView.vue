<script setup>
import { onBeforeMount, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { mdiMonitorCellphone, mdiTableBorder, mdiTableOff, mdiGithub, mdiPlus, mdiCashFast } from '@mdi/js'
import { useMainStore } from '@/stores/main'
import SectionMain from '@/components/SectionMain.vue'
import NotificationBar from '@/components/NotificationBar.vue'
import TableSales from '@/components/TableSales.vue'
import CardBox from '@/components/CardBox.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import BaseButton from '@/components/BaseButton.vue'
import axios from 'axios'

const mainStore = useMainStore()
const router = useRouter()

// Verificar se é Admin para mostrar o botão de pagamentos
const isAdmin = computed(() => localStorage.getItem('isAdmin') === 'true')

onBeforeMount(() => {
  if(localStorage.getItem('isAdmin') == 'true'){
    mainStore.getAdminOverview()
  }else{
    mainStore.getUserInfo()
  }
})

const newSale = () => {
  router.push('/sales/new')
}

// Função para processar pagamentos automáticos (DDT)
const processPayments = async () => {
  if (!confirm("Tem a certeza que deseja processar os pagamentos pendentes? Esta ação é auditada.")) return;

  try {
    // Simulação de Assinatura Digital do Cliente
    // Num cenário real: window.crypto.subtle.sign(privateKey, token)
    // Para teste, enviamos uma hash simulada que o backend deve validar
    const mockSignature = "a1b2c3d4e5f67890abcdef1234567890"

    const response = await axios.post('http://localhost:5000/company/pay', {
      token: localStorage.getItem('token')
    }, {
      headers: {
        'X-Admin-Signature': mockSignature // Header obrigatório para Não-Repúdio
      }
    })

    if (response.status === 200) {
      alert("Pagamentos processados com sucesso! ID Transação: " + response.data.details.transaction_id)
    }
  } catch (error) {
    const msg = error.response?.data?.error || "Erro ao processar pagamentos."
    alert("Erro: " + msg)
  }
}

</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton :icon="mdiTableBorder" title="Sales" main>
        <div class="flex gap-2">
          <BaseButton
            v-if="isAdmin"
            :icon="mdiCashFast"
            label="Process Payments"
            color="danger"
            rounded-full
            small
            @click="processPayments"
          />

          <BaseButton
            target="_blank"
            :icon="mdiPlus"
            label="New sale"
            color="success"
            rounded-full
            small
            @click="newSale"
          />
        </div>
      </SectionTitleLineWithButton>

      <CardBox class="mb-6" has-table>
        <TableSales />
      </CardBox>
    </SectionMain>
  </LayoutAuthenticated>
</template>
