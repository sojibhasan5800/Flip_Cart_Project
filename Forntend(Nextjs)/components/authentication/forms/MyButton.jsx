import * as React from 'react'
import Button from '@mui/material/Button'

export default function MyButton({ label, type }) {
  return (
    <Button variant="contained" type={type} fullWidth>
      {label}
    </Button>
  )
}
