<script setup>
import { computed, reactive, ref } from 'vue'
import { mdiAccount, mdiEmail, mdiIdCard, mdiMapMarker, mdiCity, mdiPhone, mdiBank, mdiClose } from '@mdi/js'
import FormField from '@/components/FormField.vue'
import FormControl from '@/components/FormControl.vue'
import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import CardBox from '@/components/CardBox.vue'
import OverlayLayer from '@/components/OverlayLayer.vue'
import CardBoxComponentTitle from '@/components/CardBoxComponentTitle.vue'

const props = defineProps({
  title: {
    type: String,
    required: true
  },
  button: {
    type: String,
    default: 'info'
  },
  buttonLabel: {
    type: String,
    default: 'Create Client'
  },
  hasCancel: Boolean,
  modelValue: {
    type: [String, Number, Boolean],
    default: null
  }
})

// Estrutura corrigida para coincidir com a API
const form = reactive({
  first_name: '',
  last_name: '',
  email: '',
  phone_number: '',
  address: '',
  city: '',
  country: '',
  iban: '' // Novo campo
})

const emit = defineEmits(['update:modelValue', 'cancel', 'confirm'])

const value = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const confirmCancel = (mode) => {
  if (mode === 'confirm') {
    // Validação básica de IBAN antes de enviar
    if (form.iban && (!form.iban.startsWith('PT50') || form.iban.length !== 25)) {
      alert('IBAN inválido. Deve começar por PT50 e ter 25 caracteres.')
      return
    }
    // Emitir os dados do formulário para o pai
    emit('confirm', { ...form })
  } else {
    emit(mode)
  }
  value.value = false
}

const confirm = () => confirmCancel('confirm')
const cancel = () => confirmCancel('cancel')

window.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && value.value) {
    cancel()
  }
})
</script>

<template>
  <OverlayLayer v-show="value" @overlay-click="cancel">
    <CardBox
      v-show="value"
      class="shadow-lg max-h-modal w-11/12 md:w-3/5 lg:w-2/5 xl:w-4/12 z-50 flex flex-col"
      is-modal
      is-form
      @submit.prevent="confirm"
    >
      <CardBoxComponentTitle :title="title">
        <BaseButton
          v-if="hasCancel"
          :icon="mdiClose"
          color="whiteDark"
          small
          rounded-full
          @click.prevent="cancel"
        />
      </CardBoxComponentTitle>

      <div class="space-y-3 flex-grow overflow-y-auto p-2">

        <FormField label="Full Name">
          <FormControl v-model="form.first_name" :icon="mdiAccount" placeholder="First Name" required />
          <FormControl v-model="form.last_name" :icon="mdiAccount" placeholder="Last Name" required />
        </FormField>

        <FormField label="Contacts">
          <FormControl v-model="form.email" :icon="mdiEmail" type="email" placeholder="Email" required />
          <FormControl v-model="form.phone_number" :icon="mdiPhone" placeholder="Phone" />
        </FormField>

        <FormField label="Address">
          <FormControl v-model="form.address" :icon="mdiMapMarker" placeholder="Street Address" />
        </FormField>

        <FormField>
          <FormControl v-model="form.city" :icon="mdiCity" placeholder="City" />
          <FormControl v-model="form.country" :icon="mdiMapMarker" placeholder="Country" />
        </FormField>

        <div class="border-t border-gray-100 pt-4 mt-4">
          <h3 class="font-bold text-gray-700 mb-2">Payment Information</h3>
          <FormField label="IBAN (Automatic Payments)" help="Format: PT50...">
            <FormControl
              v-model="form.iban"
              :icon="mdiBank"
              placeholder="PT50000000000000000000000"
              maxlength="25"
            />
          </FormField>
        </div>

      </div>

      <template #footer>
        <BaseButtons class="mt-4">
          <BaseButton :label="buttonLabel" :color="button" type="submit" />
          <BaseButton v-if="hasCancel" label="Cancel" :color="button" outline @click="cancel" />
        </BaseButtons>
      </template>
    </CardBox>
  </OverlayLayer>
</template>
