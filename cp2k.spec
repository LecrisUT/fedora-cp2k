%global svn 15878
%global snapshot 20150911
# TODO OpenCL support: -D__ACC -D__DBCSR_ACC -D__OPENCL

Name: cp2k
Version: 2.7.0
Release: 0.4.%{snapshot}svn%{svn}%{?dist}
Group: Applications/Engineering
Summary: Ab Initio Molecular Dynamics
License: GPLv2+
URL: http://cp2k.org/
%if %{svn}
# run cp2k-snapshot.sh to produce this
Source0: cp2k-%{version}-%{snapshot}.tar.xz
%else
Source0: http://downloads.sourceforge.net/project/cp2k/cp2k-%{version}.tar.bz2
Source1: http://downloads.sourceforge.net/project/cp2k/testresults/cp2k-2_6_1-branch_LAST-Linux-x86-64-gfortran-pdbg.tar.bz2
%endif
Source4: cp2k-snapshot.sh
# patch to:
# use rpm optflags
# link with atlas instead of vanilla blas/lapack
# build with libint and libxc
# skip compilation during regtests
Patch0: %{name}-rpm.patch
# build shared libraries
Patch1: cp2k-shared.patch
# don't assume Linux/ppc64 is Linux-bgl-ibm
Patch2: cp2k-ppc64.patch
BuildRequires: atlas-devel >= 3.10.1
# for regtests
BuildRequires: bc
BuildRequires: fftw-devel
BuildRequires: gcc-gfortran
BuildRequires: libint-devel >= 1.1.4
BuildRequires: libxc-devel
BuildRequires: python
BuildRequires: /usr/bin/hostname

# Libint can break the API between releases
Requires: libint(api)%{?_isa} = %{_libint_apiversion}

Requires: %{name}-common = %{version}-%{release}
Obsoletes: %{name}-smp < 2.4-3
Provides: %{name}-smp = %{version}-%{release}
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

%global cp2k_desc_base \
CP2K is a freely available (GPL) program, written in Fortran 95, to\
perform atomistic and molecular simulations of solid state, liquid,\
molecular and biological systems. It provides a general framework for\
different methods such as e.g. density functional theory (DFT) using a\
mixed Gaussian and plane waves approach (GPW), and classical pair and\
many-body potentials.\
\
CP2K does not implement Car-Parinello Molecular Dynamics (CPMD).

%description
%{cp2k_desc_base}

This package contains the non-MPI single process and multi-threaded versions.

%package openmpi
Group: Applications/Engineering
Summary: Molecular simulations software - openmpi version
BuildRequires:  openmpi-devel
BuildRequires:  blacs-openmpi-devel
BuildRequires:  elpa-openmpi-devel >= 2015.02.001
BuildRequires:  scalapack-openmpi-devel
Requires: %{name}-common = %{version}-%{release}
# Libint may have API breakage
Requires: libint(api)%{?_isa} = %{_libint_apiversion}

%description openmpi
%{cp2k_desc_base}

This package contains the parallel single- and multi-threaded versions
using OpenMPI.

%package mpich
Group: Applications/Engineering
Summary: Molecular simulations software - mpich version
BuildRequires:  mpich-devel
BuildRequires:  blacs-mpich-devel
BuildRequires:  elpa-mpich-devel >= 2015.02.001
BuildRequires:  scalapack-mpich-devel
Requires: %{name}-common = %{version}-%{release}
Provides: %{name}-mpich2 = %{version}-%{release}
Obsoletes: %{name}-mpich2 < 2.4-5
# Libint may have API breakage
Requires: libint(api)%{?_isa} = %{_libint_apiversion}

%description mpich
%{cp2k_desc_base}

This package contains the parallel single- and multi-threaded versions
using mpich.

%package common
Group: Applications/Engineering
Summary: Molecular simulations software - common files

%description common
%{cp2k_desc_base}

This package contains the documentation and the manual.

%prep
%setup -q
%patch0 -p1 -b .r
%patch1 -p1 -b .shared
%patch2 -p1 -b .ppc64

%if 0%{?fedora}
sed -i 's|-lmpiblacsF77init||g;s|-lmpiblacsCinit||g' arch/Linux-x86-64-gfortran*
%endif

# Generate necessary symlinks
TARGET=$(tools/build_utils/get_arch_code)
%ifnarch x86_64
ln -s Linux-x86-64-gfortran.sopt arch/${TARGET}.sopt
ln -s Linux-x86-64-gfortran.ssmp arch/${TARGET}.ssmp
%endif
ln -s Linux-x86-64-gfortran.popt arch/${TARGET}-openmpi.popt
ln -s Linux-x86-64-gfortran.popt arch/${TARGET}-mpich.popt
ln -s Linux-x86-64-gfortran.psmp arch/${TARGET}-openmpi.psmp
ln -s Linux-x86-64-gfortran.psmp arch/${TARGET}-mpich.psmp

# fix crashes in fftw on i686. Need to run on original file, otherwise symlinks will be replaced with copies.
%ifarch i686
sed -i 's/-D__FFTW3/-D__FFTW3 -D__FFTW3_UNALIGNED/g' arch/Linux-x86-64-gfortran*
%endif

# See cp2k/tools/hfx_tools/libint_tools/README_LIBINT
# Get libint and libderiv limits
maxam=`awk '/LIBINT_MAX_AM / {print $3}' %{_includedir}/libint/libint.h`
maxderiv=`awk '/LIBDERIV_MAX_AM1 / {print $3}' %{_includedir}/libderiv/libderiv.h`
# Plug them in the configuration
for f in arch/Linux-x86-64-gfortran.{popt,psmp,sopt,ssmp}; do
 sed -i "s|@LIBINT_MAX_AM@|$maxam|g;s|@LIBDERIV_MAX_AM@|$maxderiv|g" $f
done

%if ! %{svn}
tar -xf %{SOURCE1}
ln -s LAST-Linux-x86-64-gfortran-regtest-pdbg LAST-${TARGET}-openmpi-psmp
%endif

%build
TARGET=$(tools/build_utils/get_arch_code)
OPTFLAGS_COMMON="%{optflags} -L%{_libdir}/atlas -fPIC"
for v in opt smp ; do
pushd makefiles
    %{_openmpi_load}
        make OPTFLAGS="${OPTFLAGS_COMMON} -I%{_fmoddir}/openmpi" %{?_smp_mflags} ARCH="${TARGET}-openmpi" VERSION=p${v}
    %{_openmpi_unload}
    %{_mpich_load}
        make OPTFLAGS="${OPTFLAGS_COMMON} -I%{_fmoddir}/mpich" %{?_smp_mflags} ARCH="${TARGET}-mpich" VERSION=p${v}
    %{_mpich_unload}

    make OPTFLAGS="${OPTFLAGS_COMMON}" %{?_smp_mflags} ARCH="${TARGET}" VERSION=s${v}
popd
done

%install
TARGET=$(tools/build_utils/get_arch_code)
for v in opt smp ; do
%{_openmpi_load}
    mkdir -p %{buildroot}{${MPI_BIN},${MPI_LIB}}
    install -pm755 exe/${TARGET}-openmpi/cp2k.p${v} %{buildroot}${MPI_BIN}/cp2k.p${v}_openmpi
    install -pm755 exe/${TARGET}-openmpi/cp2k_shell.p${v} %{buildroot}${MPI_BIN}/cp2k_shell.p${v}_openmpi
    install -pm755 lib/${TARGET}-openmpi/p${v}/lib*.p${v}.so.* %{buildroot}${MPI_LIB}/
%{_openmpi_unload}
%{_mpich_load}
    mkdir -p %{buildroot}{${MPI_BIN},${MPI_LIB}}
    install -pm755 exe/${TARGET}-mpich/cp2k.p${v} %{buildroot}${MPI_BIN}/cp2k.p${v}_mpich
    install -pm755 exe/${TARGET}-mpich/cp2k_shell.p${v} %{buildroot}${MPI_BIN}/cp2k_shell.p${v}_mpich
    install -pm755 lib/${TARGET}-mpich/p${v}/lib*.p${v}.so.* %{buildroot}${MPI_LIB}/
%{_mpich_unload}
mkdir -p %{buildroot}{%{_bindir},%{_libdir},%{_datadir}/cp2k}
install -pm755 exe/${TARGET}/cp2k.s${v} %{buildroot}%{_bindir}
install -pm755 exe/${TARGET}/cp2k_shell.s${v} %{buildroot}%{_bindir}
install -pm755 lib/${TARGET}/s${v}/lib*.s${v}.so.* %{buildroot}%{_libdir}/
cp -pr data/* %{buildroot}%{_datadir}/cp2k/
done

%clean
rm -rf %{buildroot}

%if 1
# regtests take 11+ hours on armv7hl
%ifnarch armv7hl
%check
cat > tests/fedora.config << __EOF__
export LC_ALL=C
dir_base=%{_builddir}
cp2k_version=psmp
export OMP_NUM_THREADS=2
numprocs=2
cp2k_run_prefix="mpiexec -np \${numprocs}"
dir_triplet=`tools/build_utils/get_arch_code`-openmpi
cp2k_dir=cp2k-%{version}
maxtasks=$(nproc)
emptycheck="NO"
leakcheck="NO"
__EOF__
pushd tests
%{_openmpi_load}
export CP2K_DATA_DIR=%{buildroot}/usr/share/cp2k/
export LD_LIBRARY_PATH=%{LD_LIBRARY_PATH}:%{buildroot}${MPI_LIB}
../tools/regtesting/do_regtest -nosvn -nobuild -config fedora.config
%{_openmpi_unload}
popd
%endif
%endif

%files common
%defattr(-,root,root,-)
%doc COPYRIGHT README
%{_datadir}/cp2k

%files
%defattr(-,root,root,-)
%{_bindir}/cp2k.sopt
%{_bindir}/cp2k.ssmp
%{_bindir}/cp2k_shell.sopt
%{_bindir}/cp2k_shell.ssmp
%{_libdir}/lib*.sopt.so.*
%{_libdir}/lib*.ssmp.so.*

%files openmpi
%defattr(-,root,root,-)
%{_libdir}/openmpi%{?_opt_cc_suffix}/bin/cp2k.popt_openmpi
%{_libdir}/openmpi%{?_opt_cc_suffix}/bin/cp2k.psmp_openmpi
%{_libdir}/openmpi%{?_opt_cc_suffix}/bin/cp2k_shell.popt_openmpi
%{_libdir}/openmpi%{?_opt_cc_suffix}/bin/cp2k_shell.psmp_openmpi
%{_libdir}/openmpi%{?_opt_cc_suffix}/lib/lib*.popt.so.*
%{_libdir}/openmpi%{?_opt_cc_suffix}/lib/lib*.psmp.so.*

%files mpich
%defattr(-,root,root,-)
%{_libdir}/mpich%{?_opt_cc_suffix}/bin/cp2k.popt_mpich
%{_libdir}/mpich%{?_opt_cc_suffix}/bin/cp2k.psmp_mpich
%{_libdir}/mpich%{?_opt_cc_suffix}/bin/cp2k_shell.popt_mpich
%{_libdir}/mpich%{?_opt_cc_suffix}/bin/cp2k_shell.psmp_mpich
%{_libdir}/mpich%{?_opt_cc_suffix}/lib/lib*.popt.so.*
%{_libdir}/mpich%{?_opt_cc_suffix}/lib/lib*.psmp.so.*

%changelog
* Wed Feb 03 2016 Fedora Release Engineering <releng@fedoraproject.org> - 2.7.0-0.4.20150911svn15878
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Tue Sep 29 2015 Peter Robinson <pbrobinson@fedoraproject.org> 2.7.0-0.3.20150911svn15878
- Rebuild (MPI)

* Fri Sep 11 2015 Dominik Mierzejewski <rpm@greysector.net> - 2.7.0-0.2.20150911svn15878
- update to SVN trunk HEAD (r15878)
- drop obsolete patch
- fix ppc64 platform detection
- don't run regtests on armv7hl for now (too slow)

* Tue Sep 08 2015 Dominik Mierzejewski <rpm@greysector.net> - 2.7.0-0.1.20150908svn15859
- update to SVN trunk HEAD (r15859)
- drop obsolete patch
- build shared libraries and include cp2k_shell
- include data files
- fix compilation of MPI code on 32-bit platforms

* Mon Aug 24 2015 Dominik Mierzejewski <rpm@greysector.net> - 2.6.1-1
- update to 2.6.1
- drop obsolete patch
- use psmp build for regtesting
- make our regtesting config more similar to upstream

* Sun Aug 16 2015 Zbigniew Jędrzejewski-Szmek <zbyszek@in.waw.pl> - 2.6.0-6
- Rebuild for MPI provides

* Mon Jul 27 2015 Sandro Mani <manisandro@gmail.com> - 2.6.0-5
- Rebuild for RPM MPI Requires Provides Change

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.6.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Sat May 02 2015 Kalev Lember <kalevlember@gmail.com> - 2.6.0-3
- Rebuilt for GCC 5 C++11 ABI change

* Fri May 01 2015 Dominik Mierzejewski <rpm@greysector.net> - 2.6.0-2
- re-enable tests on i686 and armv7hl, they seem to complete now

* Tue Mar 17 2015 Dominik Mierzejewski <rpm@greysector.net> - 2.6.0-1
- update to 2.6.0 release
- makedepf90 no longer required (replaced with python script)
- drop upstreamed patch
- backport fixes from 2.6 stable branch

* Mon Mar 16 2015 Thomas Spura <tomspur@fedoraproject.org> - 2.5.1-11
- Rebuild for changed mpich libraries

* Tue Oct 14 2014 Dominik Mierzejewski <rpm@greysector.net> - 2.5.1-10
- add Linux on non-x86 support to tools/get_arch_code

* Tue Sep 09 2014 Susi Lehtola <jussilehtola@fedoraproject.org> - 2.5.1-9
- Requires: libint(api).

* Sat Aug 16 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.5.1-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Tue Jun 24 2014 Dominik Mierzejewski <rpm@greysector.net> - 2.5.1-7
- add ELPA support
- fix download link for reference test data

* Wed Jun 18 2014 Dominik Mierzejewski <rpm@greysector.net> - 2.5.1-6
- rebuild for libint

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.5.1-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Tue May 20 2014 Thomas Spura <tomspur@fedoraproject.org> - 2.5.1-4
- run tests with openmpi on 2 cores

* Tue May 13 2014 Thomas Spura <tomspur@fedoraproject.org> - 2.5.1-3
- add upstream reference data for evaluating tests

* Mon May 12 2014 Tom Callaway <spot@fedoraproject.org> - 2.5.1-2
- compile against new blacs in rawhide

* Fri Mar 14 2014 Dominik Mierzejewski <rpm@greysector.net> - 2.5.1-1
- update to upstream 2.5.1 release
- drop backported compilation fix

* Tue Mar 11 2014 Dominik Mierzejewski <rpm@greysector.net> - 2.5.0-1
- update to upstream 2.5 release
- backport compilation fix from SVN
- fix description (cp2k doesn't implement Car-Parinello Molecular Dynamics)

* Mon Mar 10 2014 Susi Lehtola <jussilehtola@fedoraproject.org> - 2.5-0.5.20131112svn13316
- Rebuild against updated libint.

* Sat Feb 22 2014 Deji Akingunola <dakingun@gmail.com> - 2.5-0.4.20131112svn13316
- Rebuild for mpich-3.1

* Mon Dec 23 2013 Susi Lehtola <jussilehtola@fedoraproject.org> - 2.5-0.3.20131112svn13316
- Rebuild against new libint.

* Fri Nov 15 2013 Dominik Mierzejewski <rpm@greysector.net> - 2.5-0.2.20131112svn13316
- use xz to compress SVN snapshot tarball

* Wed Nov 13 2013 Dominik Mierzejewski <rpm@greysector.net> - 2.5-0.1.20131112svn13316
- update to current SVN trunk
- fix build against atlas >= 3.10.1
- use non-threaded atlas for OpenMP builds per upstream recommendation
- fix BR broken by UsrMove feature

* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.4-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Sat Jul 20 2013 Deji Akingunola <dakingun@gmail.com> - 2.4-5
- Rename mpich2 sub-packages to mpich and rebuild for mpich-3.0

* Sun Jul 14 2013 Dominik Mierzejewski <rpm@greysector.net> - 2.4-4
- rebuild for new OpenMPI

* Tue Jul 02 2013 Dominik Mierzejewski <rpm@greysector.net> - 2.4-3
- build psmp variants (MPI+OpenMP)
- move ssmp build to main package and drop smp subpackage
- drop local config files, patch upstream's and symlink when necessary
- save the output of tools/get_arch_code and re-use it

* Wed Jun 19 2013 Dominik Mierzejewski <rpm@greysector.net> - 2.4-2
- add MPI implementation suffix back to MPI binaries (required by guidelines)

* Mon Jun 17 2013 Dominik Mierzejewski <rpm@greysector.net> - 2.4-1
- update to 2.4 release
- drop gfortran-4.8 patch (fixed upstream)
- reorder libraries in LDFLAGS again to follow current upstream config
- rename both MPI binaries to cp2k.popt

* Thu Apr 18 2013 Dominik Mierzejewski <rpm@greysector.net> - 2.4-0.5.20130418
- correct SVN url in snapshot script
- update to current SVN trunk (r12842)
- use (and patch) upstream-provided configs for x86_64 ssmp and popt builds
- no need to force FC=gfortran anymore

* Wed Apr 17 2013 Dominik Mierzejewski <rpm@greysector.net> - 2.4-0.4.20130220
- fix build with gfortran-4.8 (bug #913927)
- link with libf77blas for MPI builds to avoid undefined reference to symbol 'dgemm_'

* Sun Apr 14 2013 Dominik Mierzejewski <rpm@greysector.net> - 2.4-0.3.20130220
- fix crashes in fftw on i686 (patch by Michael Banck)

* Fri Feb 22 2013 Dominik Mierzejewski <rpm@greysector.net> - 2.4-0.2.20130220
- add requires for respective blacs and scalapack versions

* Wed Feb 20 2013 Dominik Mierzejewski <rpm@greysector.net> - 2.4-0.1.20130220
- re-enable regtests
- update to current SVN trunk (2.4)
- drop svn patch (no longer needed)
- link with libfftw3_omp for ssmp build
- reorder libraries in LDFLAGS per M. Guidon's cp2k installation primer
- add -ffree-line-length-none to Fortran flags
- add a patch to echo the name of reach test (from Debian package)
- build with libxc
- update libint/libderiv options to match current builds

* Wed Feb 13 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.3-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Wed Dec 26 2012 Kevin Fenzi <kevin@scrye.com> 2.3-2
- Rebuild for new libmpich

* Wed Sep 05 2012 Dominik Mierzejewski <rpm@greysector.net> - 2.3-1
- updated to 2.3 release

* Sun Aug 26 2012 Dominik Mierzejewski <rpm@greysector.net> - 2.3-0.20120825
- updated to current 2.3 branch (trunk)
- added snapshot creator script
- moved new files out of -rpm patch and into separate SourceN entries
- dropped non-standard compiler flags from MPI builds

* Wed Jul 25 2012 Jussi Lehtola <jussilehtola@fedoraproject.org> - 2.1-7.20101006
- Rebuild due to changed libint.

* Tue Jul 24 2012 Thomas Spura <tomspur@fedoraproject.org> - 2.1-6.20101006
- don't run testsuite as it is only usefull when comparing to old outputs
  (which we don't have at buildtime)
- define common description macro
- also build with openmpi/mpich2
- new url

* Wed Jul 18 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.1-5.20101006
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Thu Jan 12 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.1-4.20101006
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Tue Feb 08 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.1-3.20101006
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Tue Dec 07 2010 Dominik Mierzejewski <rpm@greysector.net> 2.1-2.20101006
- make Summary more descriptive
- use atlas instead of blas/lapack
- pass special CFLAGS to support libint's higher values of angular momentum

* Fri Dec 03 2010 Dominik Mierzejewski <rpm@greysector.net> 2.1-1.20101006
- initial package
