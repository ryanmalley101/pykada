from termcolor import cprint

from pykada.core_command import *
from pykada.helpers import generate_random_alphanumeric_string

current_time = int(time.time())
one_hour_ago = current_time - 3600



def get_audit_log_test():
    """
    Test function to retrieve audit logs.
    """
    # Example usage of the get_audit_logs function
    response = get_all_audit_logs(start_time=one_hour_ago-3600,
                              end_time=one_hour_ago)
    print("Audit Logs:", list(response))


def command_user_crud_test():
    """
    Test function to create, update, and delete a user.
    """
    # new_user_external_id = str(uuid.uuid4())
    new_user_external_id = generate_random_alphanumeric_string()  # Replace with a valid external ID

    # Example usage of the create_user function
    new_user = create_user(external_id=new_user_external_id,
                           company_name="ACME Corp",
                           department="Engineering",
                           department_id="12345",
                           email=f"{new_user_external_id}@example.com",
                           employee_id="E12345",
                           employee_type="full-time",
                           employee_title="Software Engineer",
                           first_name="John",
                           middle_name="A",
                           last_name="Doe",
                           )
    print("New User:", new_user)

    try:
        # Example usage of the get_user function
        user = get_user(external_id=new_user_external_id)
        print("User:", user)

        # Example usage of the update_user function
        updated_user = update_user(external_id=new_user_external_id,
                                    company_name = "Placeholder Corp",
                                    department = "Placeholder Department",
                                    department_id = "00000",
                                    email=f"{new_user_external_id}@example.com",
                                    employee_id = "EMP00000",
                                    employee_type = "contractor",
                                    employee_title = "Placeholder Title",
                                    first_name = "Placeholder",
                                    middle_name = "M",
                                    last_name = "User")

        print("Updated User:", updated_user)
    finally:
        # Example usage of the delete_user function
        delete_response = delete_user(external_id=new_user_external_id)
        print("Delete Response:", delete_response)

    cprint("User CRUD test was successful.", "green")

get_audit_log_test()
command_user_crud_test()
