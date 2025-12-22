<script setup>
import { reactive, ref } from 'vue'
import { mdiAccount, mdiEmail, mdiPhone, mdiMapMarker, mdiCity, mdiBank, mdiContentSave, mdiArrowLeft } from '@mdi/js'
import SectionMain from '@/components/SectionMain.vue'
import CardBox from '@/components/CardBox.vue'
import FormField from '@/components/FormField.vue'
import FormControl from '@/components/FormControl.vue'
import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

const router = useRouter()

const form = reactive({
  first_name: '',
  last_name: '',
  email: '',
  phone_number: '',
  address: '',
  city: '',
  country: '',
  iban: '' // Campo Novo
})

const submit = () => {
  // Validação simples de IBAN no Frontend
  if (form.iban && (!form.iban.startsWith('PT50') || form.iban.length !== 25)) {
    alert('Formato de IBAN inválido. Deve começar por PT50 e ter 25 caracteres.')
    return
  }

  const payload = {
    ...form,
    token: localStorage.getItem('token') // Autenticação
  }

  axios
    .post('http://localhost:5000/clients/new', payload)
    .then((r) => {
      if (r.data.status === 'Ok') {
        alert('Client created successfully!')
        router.push('/clients')
      } else {
        alert('Error creating client.')
      }
    })
    .catch((e) => {
      alert(e.response?.data?.error || e.message)
    })
}
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton :icon="mdiAccount" title="New Client" main>
        <BaseButton
          :icon="mdiArrowLeft"
          label="Back"
          color="whiteDark"
          rounded-full
          small
          @click="router.back()"
        />
      </SectionTitleLineWithButton>

      <CardBox is-form @submit.prevent="submit">
        <FormField label="Personal Information">
          <FormControl v-model="form.first_name" :icon="mdiAccount" placeholder="First Name" required />
          <FormControl v-model="form.last_name" :icon="mdiAccount" placeholder="Last Name" required />
        </FormField>

        <FormField label="Contact Information">
          <FormControl v-model="form.email" :icon="mdiEmail" type="email" placeholder="Email" required />
          <FormControl v-model="form.phone_number" :icon="mdiPhone" placeholder="Phone Number" />
        </FormField>

        <FormField label="Address">
          <FormControl v-model="form.address" :icon="mdiMapMarker" placeholder="Address" />
          <FormControl v-model="form.city" :icon="mdiCity" placeholder="City" />
          <FormControl v-model="form.country" :icon="mdiMapMarker" placeholder="Country" />
        </FormField>

        <div class="my-6 border-t border-gray-100 pt-6">
          <h2 class="text-lg font-bold text-gray-700 mb-4">Payment Data</h2>
          <FormField label="IBAN (Para pagamentos automáticos)" help="Formato: PT50... (25 dígitos)">
            <FormControl
              v-model="form.iban"
              :icon="mdiBank"
              placeholder="PT50000000000000000000000"
              maxlength="25"
            />
          </FormField>
        </div>

        <template #footer>
          <BaseButtons>
            <BaseButton type="submit" color="info" label="Create Client" :icon="mdiContentSave" />
            <BaseButton type="reset" color="info" outline label="Reset" />
          </BaseButtons>
        </template>
      </CardBox>
    </SectionMain>
  </LayoutAuthenticated>
</template>
