class EventValidator():
    def __init__(self, data, event_instance):
        self.can_edit(event_instance)
        self.validate_budget(data, event_instance)

    @classmethod
    def can_edit(cls, event_instance):
        if event_instance:
            if not event_instance.is_active_event:
                raise ValueError("Permanent record. Cannot be changed")
        return True
        
    @classmethod
    def validate_budget(cls, data, event_instance):
        add_ons = data.get('add_ons', event_instance.add_ons.all() if event_instance else [])
        total_price = sum(add_on.price for add_on in add_ons)

        package = data.get('package', event_instance.package if event_instance else None)
        total_price += package.budget if package is not None else 0

        discount = data.get('discount', event_instance.discount if event_instance else 0)
        payment_received = event_instance.payment_received if event_instance else 0
        discounted_budget = total_price - discount

        if total_price >= discount:
            if payment_received > discounted_budget:
                raise ValueError(f"The payment received for this event BDT {payment_received} is greater than the edited budget of the event BDT {discounted_budget}. First change the Cash Inflow instance.")
            return True
        raise ValueError(f"Discount (BDT {data['discount']}) should be less than the total budget (BDT {total_price}) of the event.")


class CashInflowValidator():
    def __init__(self, data, cashinflow_instance):
        self.can_edit(cashinflow_instance)
        self.validate_inflow(data, cashinflow_instance)

    @classmethod
    def can_edit(cls, cashinflow_instance):
        if cashinflow_instance and not cashinflow_instance.is_active:
            raise ValueError("Permanent record. Cannot be changed")
        return True


    @classmethod
    def validate_inflow(cls, data, cashinflow_instance):
        client = data.get('source', cashinflow_instance.source if cashinflow_instance else None)
        amount = data.get('amount', cashinflow_instance.amount if cashinflow_instance else 0)
        pending_amount = client.get_pending_payment() +  (cashinflow_instance.amount if cashinflow_instance else 0)
        if pending_amount < amount:
            raise ValueError(f"Cash Inflow amount for client {client.full_name} is greater than the pending payment of {client.get_pending_payment()}")
        

