from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from datetime import datetime, date, time
from typing import Optional, List, Dict, Any
from enum import Enum
from decimal import Decimal


# Enums for better type safety and data integrity
class EmployeeRole(str, Enum):
    EMPLOYEE = "employee"
    MANAGER = "manager"
    HR = "hr"
    ADMIN = "admin"


class EmployeeStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    TERMINATED = "terminated"
    ON_LEAVE = "on_leave"


class LeaveType(str, Enum):
    ANNUAL = "annual"
    SICK = "sick"
    MATERNITY = "maternity"
    PATERNITY = "paternity"
    EMERGENCY = "emergency"
    UNPAID = "unpaid"
    BEREAVEMENT = "bereavement"
    STUDY = "study"


class LeaveStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class AttendanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    HALF_DAY = "half_day"
    WORK_FROM_HOME = "work_from_home"


# Persistent models (stored in database)
class Department(SQLModel, table=True):
    __tablename__ = "departments"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True)
    description: str = Field(default="", max_length=500)
    manager_id: Optional[int] = Field(default=None, foreign_key="employees.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    employees: List["Employee"] = Relationship(back_populates="department")
    manager: Optional["Employee"] = Relationship(
        back_populates="managed_departments", sa_relationship_kwargs={"foreign_keys": "[Department.manager_id]"}
    )


class Employee(SQLModel, table=True):
    __tablename__ = "employees"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    employee_id: str = Field(unique=True, max_length=20, description="Company employee ID")
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    email: str = Field(unique=True, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=20)
    date_of_birth: Optional[date] = Field(default=None)
    hire_date: date = Field(description="Date when employee was hired")
    role: EmployeeRole = Field(default=EmployeeRole.EMPLOYEE)
    status: EmployeeStatus = Field(default=EmployeeStatus.ACTIVE)
    department_id: Optional[int] = Field(default=None, foreign_key="departments.id")
    manager_id: Optional[int] = Field(default=None, foreign_key="employees.id")
    salary: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=10)
    address: Optional[str] = Field(default=None, max_length=500)
    emergency_contact_name: Optional[str] = Field(default=None, max_length=100)
    emergency_contact_phone: Optional[str] = Field(default=None, max_length=20)
    profile_picture_url: Optional[str] = Field(default=None, max_length=500)
    preferences: Dict[str, Any] = Field(
        default={}, sa_column=Column(JSON), description="User preferences like theme, notifications"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    department: Optional[Department] = Relationship(back_populates="employees")
    manager: Optional["Employee"] = Relationship(
        back_populates="subordinates",
        sa_relationship_kwargs={"remote_side": "Employee.id", "foreign_keys": "[Employee.manager_id]"},
    )
    subordinates: List["Employee"] = Relationship(
        back_populates="manager", sa_relationship_kwargs={"foreign_keys": "[Employee.manager_id]"}
    )
    managed_departments: List[Department] = Relationship(
        back_populates="manager", sa_relationship_kwargs={"foreign_keys": "[Department.manager_id]"}
    )
    attendance_records: List["AttendanceRecord"] = Relationship(back_populates="employee")
    leave_requests: List["LeaveRequest"] = Relationship(
        back_populates="employee", sa_relationship_kwargs={"foreign_keys": "[LeaveRequest.employee_id]"}
    )
    approved_leave_requests: List["LeaveRequest"] = Relationship(
        back_populates="approved_by_user", sa_relationship_kwargs={"foreign_keys": "[LeaveRequest.approved_by]"}
    )
    leave_balances: List["LeaveBalance"] = Relationship(back_populates="employee")


class AttendanceRecord(SQLModel, table=True):
    __tablename__ = "attendance_records"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="employees.id")
    attendance_date: date = Field(description="Date of attendance")
    clock_in_time: Optional[time] = Field(default=None, description="Time when employee clocked in")
    clock_out_time: Optional[time] = Field(default=None, description="Time when employee clocked out")
    break_start_time: Optional[time] = Field(default=None, description="Break start time")
    break_end_time: Optional[time] = Field(default=None, description="Break end time")
    total_hours: Optional[Decimal] = Field(
        default=None, decimal_places=2, max_digits=5, description="Total hours worked"
    )
    overtime_hours: Optional[Decimal] = Field(
        default=Decimal("0"), decimal_places=2, max_digits=5, description="Overtime hours"
    )
    status: AttendanceStatus = Field(default=AttendanceStatus.PRESENT)
    location: Optional[str] = Field(default=None, max_length=200, description="Work location or IP address")
    notes: Optional[str] = Field(default=None, max_length=500, description="Additional notes")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    employee: Employee = Relationship(back_populates="attendance_records")


class LeaveBalance(SQLModel, table=True):
    __tablename__ = "leave_balances"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="employees.id")
    leave_type: LeaveType = Field(description="Type of leave")
    year: int = Field(description="Calendar year for this balance")
    allocated_days: Decimal = Field(decimal_places=1, max_digits=5, description="Total allocated days for the year")
    used_days: Decimal = Field(default=Decimal("0"), decimal_places=1, max_digits=5, description="Days already used")
    pending_days: Decimal = Field(
        default=Decimal("0"), decimal_places=1, max_digits=5, description="Days in pending requests"
    )
    carried_forward: Decimal = Field(
        default=Decimal("0"), decimal_places=1, max_digits=5, description="Days carried from previous year"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    employee: Employee = Relationship(back_populates="leave_balances")


class LeaveRequest(SQLModel, table=True):
    __tablename__ = "leave_requests"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="employees.id")
    leave_type: LeaveType = Field(description="Type of leave requested")
    start_date: date = Field(description="Start date of leave")
    end_date: date = Field(description="End date of leave")
    days_requested: Decimal = Field(decimal_places=1, max_digits=5, description="Number of days requested")
    reason: str = Field(max_length=1000, description="Reason for leave request")
    status: LeaveStatus = Field(default=LeaveStatus.PENDING)
    approved_by: Optional[int] = Field(default=None, foreign_key="employees.id")
    approval_date: Optional[datetime] = Field(default=None)
    approval_notes: Optional[str] = Field(default=None, max_length=500)
    supporting_documents: List[str] = Field(
        default=[], sa_column=Column(JSON), description="URLs to supporting documents"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    employee: Employee = Relationship(
        back_populates="leave_requests", sa_relationship_kwargs={"foreign_keys": "[LeaveRequest.employee_id]"}
    )
    approved_by_user: Optional[Employee] = Relationship(
        back_populates="approved_leave_requests", sa_relationship_kwargs={"foreign_keys": "[LeaveRequest.approved_by]"}
    )


class Holiday(SQLModel, table=True):
    __tablename__ = "holidays"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=200, description="Name of the holiday")
    holiday_date: date = Field(description="Date of the holiday")
    is_recurring: bool = Field(default=True, description="Whether holiday repeats annually")
    is_optional: bool = Field(default=False, description="Whether holiday is optional")
    description: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class WorkShift(SQLModel, table=True):
    __tablename__ = "work_shifts"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, description="Shift name (e.g., Morning, Evening)")
    start_time: time = Field(description="Shift start time")
    end_time: time = Field(description="Shift end time")
    break_duration_minutes: int = Field(default=60, description="Break duration in minutes")
    is_default: bool = Field(default=False, description="Whether this is the default shift")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EmployeeShift(SQLModel, table=True):
    __tablename__ = "employee_shifts"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="employees.id")
    shift_id: int = Field(foreign_key="work_shifts.id")
    effective_date: date = Field(description="Date when this shift assignment becomes effective")
    end_date: Optional[date] = Field(default=None, description="Date when this shift assignment ends")
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Non-persistent schemas (for validation, forms, API requests/responses)
class EmployeeCreate(SQLModel, table=False):
    employee_id: str = Field(max_length=20)
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    email: str = Field(max_length=255)
    phone: Optional[str] = Field(default=None, max_length=20)
    date_of_birth: Optional[date] = Field(default=None)
    hire_date: date
    role: EmployeeRole = Field(default=EmployeeRole.EMPLOYEE)
    department_id: Optional[int] = Field(default=None)
    manager_id: Optional[int] = Field(default=None)
    salary: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=10)
    address: Optional[str] = Field(default=None, max_length=500)
    emergency_contact_name: Optional[str] = Field(default=None, max_length=100)
    emergency_contact_phone: Optional[str] = Field(default=None, max_length=20)


class EmployeeUpdate(SQLModel, table=False):
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    email: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=20)
    date_of_birth: Optional[date] = Field(default=None)
    role: Optional[EmployeeRole] = Field(default=None)
    status: Optional[EmployeeStatus] = Field(default=None)
    department_id: Optional[int] = Field(default=None)
    manager_id: Optional[int] = Field(default=None)
    salary: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=10)
    address: Optional[str] = Field(default=None, max_length=500)
    emergency_contact_name: Optional[str] = Field(default=None, max_length=100)
    emergency_contact_phone: Optional[str] = Field(default=None, max_length=20)
    profile_picture_url: Optional[str] = Field(default=None, max_length=500)
    preferences: Optional[Dict[str, Any]] = Field(default=None)


class AttendanceCreate(SQLModel, table=False):
    employee_id: int
    attendance_date: date
    clock_in_time: Optional[time] = Field(default=None)
    clock_out_time: Optional[time] = Field(default=None)
    status: AttendanceStatus = Field(default=AttendanceStatus.PRESENT)
    location: Optional[str] = Field(default=None, max_length=200)
    notes: Optional[str] = Field(default=None, max_length=500)


class AttendanceUpdate(SQLModel, table=False):
    clock_out_time: Optional[time] = Field(default=None)
    break_start_time: Optional[time] = Field(default=None)
    break_end_time: Optional[time] = Field(default=None)
    status: Optional[AttendanceStatus] = Field(default=None)
    location: Optional[str] = Field(default=None, max_length=200)
    notes: Optional[str] = Field(default=None, max_length=500)


class LeaveRequestCreate(SQLModel, table=False):
    employee_id: int
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: str = Field(max_length=1000)
    supporting_documents: Optional[List[str]] = Field(default=[])


class LeaveRequestUpdate(SQLModel, table=False):
    start_date: Optional[date] = Field(default=None)
    end_date: Optional[date] = Field(default=None)
    reason: Optional[str] = Field(default=None, max_length=1000)
    supporting_documents: Optional[List[str]] = Field(default=None)


class LeaveRequestApproval(SQLModel, table=False):
    status: LeaveStatus
    approval_notes: Optional[str] = Field(default=None, max_length=500)


class DepartmentCreate(SQLModel, table=False):
    name: str = Field(max_length=100)
    description: str = Field(default="", max_length=500)
    manager_id: Optional[int] = Field(default=None)


class DepartmentUpdate(SQLModel, table=False):
    name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    manager_id: Optional[int] = Field(default=None)


class LeaveBalanceCreate(SQLModel, table=False):
    employee_id: int
    leave_type: LeaveType
    year: int
    allocated_days: Decimal = Field(decimal_places=1, max_digits=5)
    carried_forward: Optional[Decimal] = Field(default=Decimal("0"), decimal_places=1, max_digits=5)


class LeaveBalanceUpdate(SQLModel, table=False):
    allocated_days: Optional[Decimal] = Field(default=None, decimal_places=1, max_digits=5)
    used_days: Optional[Decimal] = Field(default=None, decimal_places=1, max_digits=5)
    pending_days: Optional[Decimal] = Field(default=None, decimal_places=1, max_digits=5)
    carried_forward: Optional[Decimal] = Field(default=None, decimal_places=1, max_digits=5)


class HolidayCreate(SQLModel, table=False):
    name: str = Field(max_length=200)
    holiday_date: date
    is_recurring: bool = Field(default=True)
    is_optional: bool = Field(default=False)
    description: Optional[str] = Field(default=None, max_length=500)


class WorkShiftCreate(SQLModel, table=False):
    name: str = Field(max_length=100)
    start_time: time
    end_time: time
    break_duration_minutes: int = Field(default=60)
    is_default: bool = Field(default=False)


class EmployeeShiftCreate(SQLModel, table=False):
    employee_id: int
    shift_id: int
    effective_date: date
    end_date: Optional[date] = Field(default=None)


# Response schemas for API endpoints
class EmployeeResponse(SQLModel, table=False):
    id: int
    employee_id: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str]
    role: EmployeeRole
    status: EmployeeStatus
    department_name: Optional[str] = Field(default=None)
    manager_name: Optional[str] = Field(default=None)
    hire_date: date
    created_at: str  # ISO format datetime string


class AttendanceResponse(SQLModel, table=False):
    id: int
    employee_name: str
    attendance_date: date
    clock_in_time: Optional[time]
    clock_out_time: Optional[time]
    total_hours: Optional[Decimal]
    overtime_hours: Optional[Decimal]
    status: AttendanceStatus
    location: Optional[str]


class LeaveRequestResponse(SQLModel, table=False):
    id: int
    employee_name: str
    leave_type: LeaveType
    start_date: date
    end_date: date
    days_requested: Decimal
    reason: str
    status: LeaveStatus
    approved_by_name: Optional[str] = Field(default=None)
    approval_date: Optional[str] = Field(default=None)  # ISO format datetime string
    created_at: str  # ISO format datetime string


class LeaveBalanceResponse(SQLModel, table=False):
    employee_name: str
    leave_type: LeaveType
    year: int
    allocated_days: Decimal
    used_days: Decimal
    pending_days: Decimal
    remaining_days: Decimal
    carried_forward: Decimal
