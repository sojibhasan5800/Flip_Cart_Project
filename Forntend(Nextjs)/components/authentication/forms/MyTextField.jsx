import * as React from 'react'
import TextField from '@mui/material/TextField'

export default function MyTextField({ label, value, onChange, error, helperText }) {
  return (
    <TextField
      label={label}
      value={value}
      onChange={onChange}
      variant="outlined"
      className="myForm"
      error={error}
      helperText={helperText}
      fullWidth
    />
  )
}
