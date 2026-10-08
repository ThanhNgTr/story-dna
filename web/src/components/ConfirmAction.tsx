import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogClose, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'

/** A button that asks before starting something long or irreversible. */
export function ConfirmAction({ trigger, title, description, confirmLabel, onConfirm, pending }: {
  trigger: React.ReactElement
  title: string
  description: React.ReactNode
  confirmLabel: string
  onConfirm: () => Promise<unknown> | void
  pending?: boolean
}) {
  const [open, setOpen] = useState(false)
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger render={trigger} />
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription render={<div />}>{description}</DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <DialogClose render={<Button variant="outline" />}>Để sau</DialogClose>
          <Button disabled={pending} onClick={async () => { await onConfirm(); setOpen(false) }}>{confirmLabel}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
