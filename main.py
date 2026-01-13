def divide_by_zero():
  """
  This function attempts to divide 1 by 0 and catches the resulting
  ZeroDivisionError, printing a user-friendly message.
  """
  try:
    result = 1 / 0
  except ZeroDivisionError:
    print("Division by zero is not allowed.")

divide_by_zero()
