using System;
using System.ComponentModel;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;

namespace AjazzResourceTools
{
    // The sampler owns a newly launched job, never attaches to an existing tray.
    public sealed class TrayJobAccounting : IDisposable
    {
        [StructLayout(LayoutKind.Sequential)]
        public struct Accounting
        {
            public long TotalUserTime, TotalKernelTime, PeriodUserTime, PeriodKernelTime;
            public uint PageFaults, TotalProcesses, ActiveProcesses, TerminatedProcesses;
            public double CpuSeconds
            {
                get { return (TotalUserTime + TotalKernelTime) / 10000000.0; }
            }
        }

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        private struct StartupInfo
        {
            public uint Size;
            public string Reserved, Desktop, Title;
            public uint X, Y, XSize, YSize, XChars, YChars, FillAttribute, Flags;
            public ushort ShowWindow, ReservedSize;
            public IntPtr ReservedBytes, StdIn, StdOut, StdErr;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct ProcessInfo
        {
            public IntPtr Process, Thread;
            public uint ProcessId, ThreadId;
        }

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern IntPtr CreateJobObject(IntPtr attributes, string name);
        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        private static extern bool CreateProcess(string application, StringBuilder commandLine,
            IntPtr processAttributes, IntPtr threadAttributes, bool inheritHandles,
            uint flags, IntPtr environment, string directory, ref StartupInfo startup,
            out ProcessInfo process);
        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool AssignProcessToJobObject(IntPtr job, IntPtr process);
        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern uint ResumeThread(IntPtr thread);
        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool TerminateProcess(IntPtr process, uint exitCode);
        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool QueryInformationJobObject(IntPtr job, int type,
            out Accounting info, uint size, IntPtr returned);
        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern uint WaitForSingleObject(IntPtr handle, uint timeout);
        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool CloseHandle(IntPtr handle);

        private IntPtr job;
        private IntPtr root;
        public uint ProcessId { get; private set; }

        public TrayJobAccounting(string exe, string fixedArguments)
        {
            exe = Path.GetFullPath(exe);
            job = CreateJobObject(IntPtr.Zero, null);
            if (job == IntPtr.Zero) throw new Win32Exception();
            var startup = new StartupInfo();
            startup.Size = (uint)Marshal.SizeOf(typeof(StartupInfo));
            ProcessInfo process = new ProcessInfo();
            bool resumed = false;
            try
            {
                // Assign before the first instruction can run or spawn children.
                var command = new StringBuilder("\"" + exe + "\" " + fixedArguments);
                if (!CreateProcess(exe, command, IntPtr.Zero, IntPtr.Zero, false,
                    4, IntPtr.Zero, Path.GetDirectoryName(exe), ref startup, out process))
                    throw new Win32Exception();
                root = process.Process;
                if (!AssignProcessToJobObject(job, root))
                    throw new Win32Exception();
                ProcessId = process.ProcessId;
                if (ResumeThread(process.Thread) == uint.MaxValue)
                    throw new Win32Exception();
                resumed = true;
            }
            finally
            {
                if (process.Thread != IntPtr.Zero) CloseHandle(process.Thread);
                if (!resumed)
                {
                    // Only an unsuccessfully launched, still-suspended process.
                    if (root != IntPtr.Zero) TerminateProcess(root, 1);
                    Dispose();
                }
            }
        }

        public Accounting Read()
        {
            Accounting result;
            if (!QueryInformationJobObject(job, 1, out result,
                (uint)Marshal.SizeOf(typeof(Accounting)), IntPtr.Zero))
                throw new Win32Exception();
            return result;
        }

        public bool RootExited
        {
            get
            {
                uint status = WaitForSingleObject(root, 0);
                if (status == 0) return true;
                if (status == 258) return false;
                throw new Win32Exception();
            }
        }

        public void Dispose()
        {
            // No KILL_ON_JOB_CLOSE: sampling never terminates a running tray.
            if (root != IntPtr.Zero) { CloseHandle(root); root = IntPtr.Zero; }
            if (job != IntPtr.Zero) { CloseHandle(job); job = IntPtr.Zero; }
        }
    }
}
