<script setup>
import { reactive } from 'vue'
import { useMainStore } from '@/stores/main'
import { mdiAccount, mdiMail, mdiAsterisk, mdiFormTextboxPassword, mdiGithub, mdiBank } from '@mdi/js'
import SectionMain from '@/components/SectionMain.vue'
import CardBox from '@/components/CardBox.vue'
import BaseDivider from '@/components/BaseDivider.vue'
import FormField from '@/components/FormField.vue'
import FormControl from '@/components/FormControl.vue'
import FormFilePicker from '@/components/FormFilePicker.vue'
import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import UserCard from '@/components/UserCard.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import axios from 'axios'

const mainStore = useMainStore()

const profileForm = reactive({
  name: mainStore.userName,
  email: mainStore.userEmail
})

const passwordForm = reactive({
  password_current: '',
  password: '',
  password_confirmation: ''
})

const ibanForm = reactive({
  iban: ''
})

const submitPass = () => {
  if(passwordForm.password != passwordForm.password_confirmation){
    alert("Passwords don't match")
    return;
  }

  const resetPassPayload = {
    current_password: passwordForm.password_current,
    new_password: passwordForm.password,
    token: localStorage.getItem('token'),
    user_id: localStorage.getItem('userId')
  }

  axios
    .post('http://localhost:5000/user/reset-password', resetPassPayload)
    .then(() => {
      alert('Password updated!');
    })
    .catch((error) => {
      alert(error.response?.data?.error || error.message);
  });
}

const submitIban = () => {
  if (!ibanForm.iban.startsWith('PT50') || ibanForm.iban.length !== 25) {
    alert('Invalid IBAN format. Must start with PT50 and have 25 chars.')
    return
  }

  axios.post('http://localhost:5000/user/update-iban', {
    token: localStorage.getItem('token'),
    iban: ibanForm.iban
  })
  .then(() => {
    alert('IBAN updated successfully! You are now eligible for automatic payments.')
    ibanForm.iban = ''
  })
  .catch((error) => {
    alert('Error updating IBAN: ' + (error.response?.data?.error || error.message))
  })
}
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton :icon="mdiAccount" title="Profile" main>
      </SectionTitleLineWithButton>

      <UserCard class="mb-6" />

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">

        <CardBox is-form @submit.prevent="submitPass">
          <h3 class="text-lg font-bold mb-4">Change Password</h3>
          <FormField label="Current password" help="Required. Your current password">
            <FormControl
              v-model="passwordForm.password_current"
              :icon="mdiAsterisk"
              name="password_current"
              type="password"
              required
              autocomplete="current-password"
            />
          </FormField>

          <BaseDivider />

          <FormField label="New password" help="Required. New password">
            <FormControl
              v-model="passwordForm.password"
              :icon="mdiFormTextboxPassword"
              name="password"
              type="password"
              required
              autocomplete="new-password"
            />
          </FormField>

          <FormField label="Confirm password" help="Required. New password one more time">
            <FormControl
              v-model="passwordForm.password_confirmation"
              :icon="mdiFormTextboxPassword"
              name="password_confirmation"
              type="password"
              required
              autocomplete="new-password"
            />
          </FormField>

          <template #footer>
            <BaseButtons>
              <BaseButton type="submit" color="info" label="Update Password" />
            </BaseButtons>
          </template>
        </CardBox>

        <CardBox is-form @submit.prevent="submitIban">
          <h3 class="text-lg font-bold mb-4">Payment Settings</h3>
          <p class="mb-4 text-gray-600 text-sm">
            Provide your IBAN to receive automatic commission payments.
            This data is stored with <strong>AES-256 encryption</strong>.
          </p>

          <FormField label="IBAN" help="Format: PT50... (25 digits)">
            <FormControl
              v-model="ibanForm.iban"
              :icon="mdiBank"
              name="iban"
              placeholder="PT50000000000000000000000"
              maxlength="25"
              required
            />
          </FormField>

          <template #footer>
            <BaseButtons>
              <BaseButton type="submit" color="success" label="Save Payment Info" />
            </BaseButtons>
          </template>
        </CardBox>

      </div>
    </SectionMain>
  </LayoutAuthenticated>
</template>
